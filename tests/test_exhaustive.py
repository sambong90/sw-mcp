"""Exhaustive search 테스트"""

import pytest
from itertools import product
from src.sw_mcp.types import Rune, SubStat
from src.sw_mcp.optimizer import optimize_lushen, search_builds
from src.sw_mcp.scoring import score_build


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


def test_target_a_rejects_fatal():
    """target A가 Fatal 4 + Blade 2를 거부하는지 테스트"""
    runes = []
    
    # Fatal 4개 + Blade 2개 생성
    for slot in range(1, 7):
        if slot == 2 or slot == 6:
            main_stat_id = 4  # ATK%
            main_value = 63
        elif slot == 4:
            main_stat_id = 10  # CD
            main_value = 80
        else:
            main_stat_id = 4  # ATK%
            main_value = 63
        
        # Fatal 4개, Blade 2개
        set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    # target="A"로 검색 (Rage 4 + Blade 2 필요)
    results = optimize_lushen(runes, target="A", mode="exhaustive", top_n=10)
    
    # Fatal이 있으므로 결과가 없어야 함
    assert len(results) == 0
    
    # search_builds도 테스트
    results2 = search_builds(runes, target="A", mode="exhaustive", top_n=10)
    assert len(results2) == 0


def test_exhaustive_matches_brute_force():
    """exhaustive 모드가 brute force와 일치하는지 테스트 (작은 fixture)"""
    # 매우 작은 fixture: 슬롯당 2개씩만
    runes = []
    
    for slot in range(1, 7):
        for i in range(2):  # 슬롯당 2개
            if slot == 2 or slot == 6:
                main_stat_id = 4
                main_value = 63
            elif slot == 4:
                main_stat_id = 10
                main_value = 80
            else:
                main_stat_id = 4
                main_value = 63
            
            # Rage 4 + Blade 2 구성
            if slot <= 4:
                set_id = 5  # Rage
            else:
                set_id = 4  # Blade
            
            # 첫 번째 룬은 CR 20, 두 번째는 CR 15
            cr_value = 20 if i == 0 else 15
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # exhaustive 모드로 검색
    results_exhaustive = optimize_lushen(
        runes, target="A", mode="exhaustive", top_n=100
    )
    
    # brute force로 모든 조합 검색
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = [r for r in runes if r.slot == slot]
    
    brute_force_results = []
    for combo in product(*[slot_runes[i] for i in range(1, 7)]):
        combo_list = list(combo)
        score, stats = score_build(combo_list, target="A", require_cr_100=True, require_sets=True)
        if score > 0:
            brute_force_results.append({
                "runes": combo_list,
                "score": score,
                "stats": stats
            })
    
    # 정렬
    brute_force_results.sort(key=lambda x: x["score"], reverse=True)
    results_exhaustive_sorted = sorted(results_exhaustive, key=lambda x: x["score"], reverse=True)
    
    # 결과 개수가 일치해야 함
    assert len(results_exhaustive) == len(brute_force_results)
    
    # 최고 점수가 일치해야 함
    if len(brute_force_results) > 0:
        assert results_exhaustive_sorted[0]["score"] == brute_force_results[0]["score"]


def test_all_at_best_returns_ties():
    """all_at_best가 tie를 모두 반환하는지 테스트"""
    runes = []
    
    # 동일한 스탯을 가진 룬들 생성 (tie 발생)
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
        
        # Rage 4 + Blade 2
        set_id = 5 if slot <= 4 else 4
        
        # 슬롯당 2개씩 생성 (동일한 스탯)
        for i in range(2):
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, 20, False, 0)]
            )
            runes.append(rune)
    
    # all_at_best로 검색
    results = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        objective="SCORE",
        return_policy="all_at_best",
        top_n=100
    )
    
    # 최고 점수가 모두 같아야 함
    if len(results) > 1:
        best_score = results[0]["score"]
        for result in results:
            assert result["score"] == best_score


def test_require_sets_false_allows_any_sets():
    """require_sets=False일 때 모든 세트가 허용되는지 테스트"""
    runes = []
    
    # 다양한 세트의 룬 생성 (Rage/Fatal/Blade 조건 불만족)
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
        
        # Swift 3개, Violent 3개 (세트 조건 불만족)
        set_id = 3 if slot <= 3 else 13  # Swift 3 + Violent 3
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    # require_sets=True면 결과 없음
    results_with_sets = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=True,
        constraints={"CR": 100}
    )
    assert len(results_with_sets) == 0
    
    # require_sets=False면 결과 있음 (CR>=100만 체크)
    results_no_sets = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=False,
        constraints={"CR": 100}
    )
    # CR 조건을 만족하면 결과가 있어야 함
    assert len(results_no_sets) > 0


def test_cr_100_not_hardcoded():
    """CR>=100이 hardcode되지 않고 constraints에만 의존하는지 테스트"""
    runes = []
    
    # CR < 100인 룬 생성
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
            [SubStat(9, 5, False, 0)]  # CR 5만 (총 CR < 100)
        )
        runes.append(rune)
    
    # constraints에 CR이 없으면 결과 없음 (기본 require_cr_100=True)
    results_no_cr_constraint = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        constraints={}  # CR 조건 없음
    )
    assert len(results_no_cr_constraint) == 0
    
    # constraints에 CR=50이면 결과 있음 (CR>=50만 체크)
    results_with_cr_constraint = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        constraints={"CR": 50}  # CR>=50만 체크
    )
    # CR>=50이면 결과가 있어야 함
    assert len(results_with_cr_constraint) > 0

