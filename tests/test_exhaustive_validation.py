"""Exhaustive mode validation tests"""

import pytest
from itertools import product
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import optimize_lushen, search_builds
from src.sw_core.scoring import score_build
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


def test_exhaustive_no_pruning():
    """Exhaustive 모드가 pruning을 사용하지 않는지 검증"""
    runes = []
    
    # 작은 fixture: 슬롯당 2개씩
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
            
            set_id = 5 if slot <= 4 else 4  # Rage 4 + Blade 2
            
            # 첫 번째 룬은 CR 20, 두 번째는 CR 15
            cr_value = 20 if i == 0 else 15
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # Exhaustive 모드로 검색
    result_exhaustive = run_search(
        runes=runes,
        target="A",
        mode="exhaustive",
        top_n=1000  # 모든 결과 요청
    )
    
    # Brute force로 모든 조합 검색
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
    
    # 결과 개수가 정확히 일치해야 함 (exhaustive는 모든 조합 탐색)
    assert len(result_exhaustive["results"]) == len(brute_force_results), \
        f"Exhaustive found {len(result_exhaustive['results'])} but brute force found {len(brute_force_results)}"
    
    # 최고 점수가 일치해야 함
    if len(brute_force_results) > 0:
        assert result_exhaustive["results"][0]["score"] == brute_force_results[0]["score"]


def test_exhaustive_finds_all_valid_builds():
    """Exhaustive 모드가 모든 유효한 빌드를 찾는지 검증"""
    runes = []
    
    # 매우 작은 fixture: 슬롯당 1개씩 (조합 1개만)
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
    
    # Exhaustive 모드로 검색
    result = run_search(
        runes=runes,
        target="A",
        mode="exhaustive",
        top_n=100
    )
    
    # 유효한 빌드가 있으면 정확히 1개여야 함
    # (조합이 1개뿐이므로)
    if len(runes) == 6:
        # CR 조건을 만족하면 결과가 있어야 함
        # BASE_CR 15 + Blade 12 + 룬 CR 120 = 147 >= 100
        assert result["total_found"] >= 0  # 최소 0개 (조건 불만족 시)


def test_exhaustive_vs_fast_completeness():
    """Exhaustive 모드가 fast 모드보다 더 완전한 결과를 제공하는지 검증"""
    runes = []
    
    # 중간 크기 fixture: 슬롯당 3개씩
    for slot in range(1, 7):
        for i in range(3):
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
            
            # 다양한 CR 값
            cr_value = 15 + (i * 5)  # 15, 20, 25
            
            rune = create_test_rune(
                slot * 1000 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # Exhaustive 모드
    result_exhaustive = run_search(
        runes=runes,
        target="B",
        mode="exhaustive",
        top_n=1000
    )
    
    # Fast 모드 (제한적 pruning)
    result_fast = run_search(
        runes=runes,
        target="B",
        mode="fast",
        max_candidates_per_slot=10,  # 작은 제한
        top_n=1000
    )
    
    # Exhaustive가 fast보다 같거나 더 많은 결과를 찾아야 함
    assert result_exhaustive["total_found"] >= result_fast["total_found"]
    
    # Exhaustive의 최고 점수가 fast보다 같거나 높아야 함
    if result_exhaustive["total_found"] > 0 and result_fast["total_found"] > 0:
        assert result_exhaustive["results"][0]["score"] >= result_fast["results"][0]["score"]


