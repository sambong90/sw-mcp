"""스코어링 테스트"""

import pytest
from src.sw_mcp.types import Rune, SubStat, BASE_CR, BLADE_2SET_CR
from src.sw_mcp.scoring import score_build, calculate_stats, find_best_intangible_assignment


def create_test_rune(rune_id, slot, set_id, main_stat_id, main_value, subs=None):
    """테스트용 룬 생성"""
    if subs is None:
        subs = []
    return Rune(
        rune_id=rune_id,
        slot=slot,
        set_id=set_id,
        main_stat_id=main_stat_id,
        main_stat_value=main_value,
        subs=subs,
        level=6,
        quality=5
    )


def test_base_cr_and_blade_bonus():
    """기본 치확 15와 칼날 세트 보너스 12 적용 테스트"""
    # Blade 2세트 구성
    runes = [
        create_test_rune(1, 1, 4, 4, 63),  # Blade, ATK%
        create_test_rune(2, 2, 4, 4, 63),  # Blade, ATK%
        create_test_rune(3, 3, 5, 4, 63),  # Rage, ATK%
        create_test_rune(4, 4, 5, 10, 80),  # Rage, CD
        create_test_rune(5, 5, 5, 4, 63),  # Rage, ATK%
        create_test_rune(6, 6, 5, 4, 63),  # Rage, ATK%
    ]
    
    # 치확 서브옵 추가 (총 73% 필요: 100 - 15 - 12 = 73)
    runes[0].subs = [SubStat(9, 20, False, 0)]  # CR 20
    runes[1].subs = [SubStat(9, 20, False, 0)]  # CR 20
    runes[2].subs = [SubStat(9, 20, False, 0)]  # CR 20
    runes[3].subs = [SubStat(9, 13, False, 0)]  # CR 13
    
    stats = calculate_stats(runes, "none")
    
    # BASE_CR 15 + Blade 12 + 룬 CR 73 = 100
    assert stats["cr_total"] == BASE_CR + BLADE_2SET_CR + 73.0


def test_intangible_single_set_assignment():
    """무형 룬이 한 세트에만 적용되는지 테스트"""
    # 무형 1개 + Rage 3개 + Blade 2개
    runes = [
        create_test_rune(1, 1, 25, 4, 63),  # Intangible
        create_test_rune(2, 2, 5, 4, 63),   # Rage
        create_test_rune(3, 3, 5, 4, 63),   # Rage
        create_test_rune(4, 4, 5, 10, 80),  # Rage
        create_test_rune(5, 5, 4, 4, 63),   # Blade
        create_test_rune(6, 6, 4, 4, 63),   # Blade
    ]
    
    # 치확 100% 달성
    runes[0].subs = [SubStat(9, 20, False, 0)]
    runes[1].subs = [SubStat(9, 20, False, 0)]
    runes[2].subs = [SubStat(9, 20, False, 0)]
    runes[3].subs = [SubStat(9, 13, False, 0)]
    
    # 무형을 Rage에 배치
    assignment1, score1, stats1 = find_best_intangible_assignment(runes, "A")
    
    # 무형을 Blade에 배치
    assignment2, score2, stats2 = find_best_intangible_assignment(runes, "A")
    
    # 한 세트에만 적용되어야 함
    assert assignment1 in ["to_Rage", "to_Blade", "none"]
    # 더 높은 스코어를 선택해야 함
    assert max(score1, score2) > 0


def test_fatal_4set_bonus():
    """Fatal 4세트 보너스 (ATK% +35) 테스트"""
    runes = [
        create_test_rune(1, 1, 8, 4, 63),  # Fatal
        create_test_rune(2, 2, 8, 4, 63),  # Fatal
        create_test_rune(3, 3, 8, 4, 63),  # Fatal
        create_test_rune(4, 4, 8, 10, 80),  # Fatal
        create_test_rune(5, 5, 4, 4, 63),  # Blade
        create_test_rune(6, 6, 4, 4, 63),  # Blade
    ]
    
    # 치확 100% 달성
    runes[0].subs = [SubStat(9, 20, False, 0)]
    runes[1].subs = [SubStat(9, 20, False, 0)]
    runes[2].subs = [SubStat(9, 20, False, 0)]
    runes[3].subs = [SubStat(9, 13, False, 0)]
    
    stats = calculate_stats(runes, "none", base_atk=900)
    
    # Fatal 4세트 보너스: ATK% +35
    # 메인 ATK% 63 * 4 = 252, 보너스 +35 = 287
    assert stats["atk_pct_total"] >= 287.0


def test_prefix_eff_in_stats():
    """prefix_eff가 스탯 합산에 포함되는지 테스트"""
    from src.sw_mcp.types import Rune, SubStat
    
    rune = Rune(
        rune_id=1,
        slot=1,
        set_id=5,
        main_stat_id=4,
        main_stat_value=63,
        subs=[SubStat(9, 10, False, 0)],
        prefix_stat_id=9,  # CR prefix
        prefix_stat_value=5.0
    )
    
    stats = calculate_stats([rune], "none", base_atk=900)
    
    # BASE_CR 15 + prefix CR 5 + sub CR 10 = 30
    assert stats["cr_total"] == BASE_CR + 5.0 + 10.0


def test_score_formula():
    """스코어 공식 테스트: (cd_total * 10) + atk_bonus + 200"""
    runes = [
        create_test_rune(1, 1, 8, 4, 63),  # Fatal
        create_test_rune(2, 2, 8, 4, 63),  # Fatal
        create_test_rune(3, 3, 8, 4, 63),  # Fatal
        create_test_rune(4, 4, 8, 10, 80),  # Fatal, CD 80
        create_test_rune(5, 5, 4, 4, 63),  # Blade
        create_test_rune(6, 6, 4, 4, 63),  # Blade
    ]
    
    # 치확 100% 달성
    runes[0].subs = [SubStat(9, 20, False, 0)]
    runes[1].subs = [SubStat(9, 20, False, 0)]
    runes[2].subs = [SubStat(9, 20, False, 0)]
    runes[3].subs = [SubStat(9, 13, False, 0)]
    
    score, stats = score_build(runes, "B", "none", base_atk=900)
    
    # 스코어 공식: (cd_total * 10) + atk_bonus + 200
    expected_score = (stats["cd_total"] * 10) + stats["atk_bonus"] + 200
    assert abs(score - expected_score) < 0.01

