"""범용 엔진 테스트"""

import pytest
from itertools import product
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import search_builds
from src.sw_core.scoring import score_build, calculate_stats
from src.sw_core.rules import validate_rune, validate_build, slot_main_is_allowed, slot_sub_is_allowed
from src.sw_core.api import run_search


def create_test_rune(rune_id, slot, set_id, main_stat_id, main_value, subs=None, prefix_stat_id=0, prefix_stat_value=0.0):
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
        quality=5,
        prefix_stat_id=prefix_stat_id,
        prefix_stat_value=prefix_stat_value
    )


def test_slot_main_restrictions():
    """슬롯별 메인스탯 제약 테스트"""
    # Slot 2: CD/CR/RES/ACC 금지
    assert not slot_main_is_allowed(2, 10)  # CD 금지
    assert not slot_main_is_allowed(2, 9)   # CR 금지
    assert not slot_main_is_allowed(2, 11)   # RES 금지
    assert not slot_main_is_allowed(2, 12)   # ACC 금지
    assert slot_main_is_allowed(2, 4)       # ATK% 허용
    assert slot_main_is_allowed(2, 8)       # SPD 허용
    
    # Slot 4: SPD/ACC/RES 금지
    assert not slot_main_is_allowed(4, 8)   # SPD 금지
    assert not slot_main_is_allowed(4, 12)   # ACC 금지
    assert not slot_main_is_allowed(4, 11)   # RES 금지
    assert slot_main_is_allowed(4, 10)      # CD 허용
    assert slot_main_is_allowed(4, 4)       # ATK% 허용
    
    # Slot 6: SPD/CD/CR 금지
    assert not slot_main_is_allowed(6, 8)   # SPD 금지
    assert not slot_main_is_allowed(6, 10)   # CD 금지
    assert not slot_main_is_allowed(6, 9)   # CR 금지
    assert slot_main_is_allowed(6, 4)       # ATK% 허용


def test_slot_sub_restrictions():
    """슬롯별 서브스탯 제약 테스트"""
    # Slot 3: ATK%, ATK+ 금지
    assert not slot_sub_is_allowed(3, 1, 4)  # ATK% 금지
    assert not slot_sub_is_allowed(3, 1, 3)  # ATK+ 금지
    assert slot_sub_is_allowed(3, 1, 9)      # CR 허용
    
    # Slot 1: DEF%, DEF+ 금지
    assert not slot_sub_is_allowed(1, 1, 6)  # DEF% 금지
    assert not slot_sub_is_allowed(1, 1, 5)  # DEF+ 금지
    assert slot_sub_is_allowed(1, 1, 9)      # CR 허용
    
    # 메인스탯과 중복 금지
    assert not slot_sub_is_allowed(2, 4, 4)  # 메인 ATK%와 서브 ATK% 중복 금지
    assert not slot_sub_is_allowed(4, 10, 10)  # 메인 CD와 서브 CD 중복 금지


def test_validate_rune():
    """룬 검증 테스트"""
    # 유효한 룬
    rune = create_test_rune(1, 2, 5, 4, 63, [SubStat(9, 20, False, 0)])
    assert validate_rune(rune)
    
    # Slot 2에서 CD 메인 금지
    rune = create_test_rune(1, 2, 5, 10, 80, [])
    assert not validate_rune(rune)
    
    # Slot 3에서 ATK% 서브 금지
    rune = create_test_rune(1, 3, 5, 1, 1000, [SubStat(4, 20, False, 0)])
    assert not validate_rune(rune)
    
    # 메인스탯과 서브스탯 중복 금지
    rune = create_test_rune(1, 2, 5, 4, 63, [SubStat(4, 20, False, 0)])
    assert not validate_rune(rune)


def test_require_sets_false():
    """require_sets=False (모든 세트 허용) 테스트"""
    runes = []
    
    # 다양한 세트의 룬 생성
    for slot in range(1, 7):
        if slot == 2 or slot == 6:
            main_stat_id = 4
            main_value = 63
        elif slot == 4:
            main_stat_id = 10
            main_value = 80
        else:
            main_stat_id = 4
            main_value = 63
        
        # Swift, Violent 등 다양한 세트
        set_id = 3 if slot <= 3 else 13  # Swift 3 + Violent 3
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    # set_constraints=None이면 모든 세트 허용
    result = search_builds(
        runes=runes,
        set_constraints=None,  # 모든 세트 허용
        constraints={"CR": 100},
        mode="exhaustive"
    )
    
    assert result is not None
    # 결과가 있을 수 있음 (CR 조건만 만족하면)


def test_set_constraints():
    """set_constraints 테스트"""
    runes = []
    
    # Rage 4개 + Blade 2개 생성
    for slot in range(1, 7):
        if slot == 2 or slot == 6:
            main_stat_id = 4
            main_value = 63
        elif slot == 4:
            main_stat_id = 10
            main_value = 80
        else:
            main_stat_id = 4
            main_value = 63
        
        set_id = 5 if slot <= 4 else 4  # Rage 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    # Rage 4 + Blade 2 조건
    result = search_builds(
        runes=runes,
        set_constraints={"Rage": 4, "Blade": 2},
        constraints={"CR": 100},
        mode="exhaustive"
    )
    
    assert len(result) > 0
    # 모든 결과가 Rage 4 + Blade 2를 만족해야 함


def test_generic_objectives():
    """범용 objective 테스트"""
    runes = []
    
    for slot in range(1, 7):
        if slot == 2 or slot == 6:
            main_stat_id = 4
            main_value = 63
        elif slot == 4:
            main_stat_id = 10
            main_value = 80
        else:
            main_stat_id = 4
            main_value = 63
        
        set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    # ATK_TOTAL objective
    result = search_builds(
        runes=runes,
        objective="ATK_TOTAL",
        top_n=10,
        mode="exhaustive"
    )
    
    if len(result) > 1:
        for i in range(len(result) - 1):
            assert result[i]["atk_total"] >= result[i + 1]["atk_total"]


def test_exhaustive_vs_brute_force():
    """Exhaustive 모드가 brute force와 일치하는지 검증"""
    runes = []
    
    # 슬롯당 2개씩만
    for slot in range(1, 7):
        for i in range(2):
            if slot == 2 or slot == 6:
                main_stat_id = 4
                main_value = 63
            elif slot == 4:
                main_stat_id = 10
                main_value = 80
            else:
                main_stat_id = 4
                main_value = 63
            
            set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
            
            cr_value = 20 if i == 0 else 15
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # Brute force로 모든 조합 탐색
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = [r for r in runes if r.slot == slot]
    
    brute_force_results = []
    for combo in product(*[slot_runes[i] for i in range(1, 7)]):
        combo_list = list(combo)
        if not validate_build(combo_list):
            continue
        
        score, stats, _ = score_build(
            combo_list,
            objective="SCORE",
            base_atk=900,
            base_spd=104,
            constraints={"CR": 100},
            set_constraints={"Fatal": 4, "Blade": 2}
        )
        if score > 0:
            brute_force_results.append({
                "runes": combo_list,
                "score": score,
                "stats": stats
            })
    
    # 정렬
    brute_force_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Exhaustive 모드로 검색
    exhaustive_results = search_builds(
        runes=runes,
        base_atk=900,
        base_spd=104,
        constraints={"CR": 100},
        set_constraints={"Fatal": 4, "Blade": 2},
        objective="SCORE",
        top_n=1000,
        mode="exhaustive"
    )
    
    # 결과 개수가 정확히 일치해야 함
    assert len(exhaustive_results) == len(brute_force_results), \
        f"Exhaustive found {len(exhaustive_results)} but brute force found {len(brute_force_results)}"
    
    # 최고 점수가 일치해야 함
    if len(brute_force_results) > 0:
        assert exhaustive_results[0]["score"] == brute_force_results[0]["score"]

