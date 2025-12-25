"""제약조건 기반 탐색 정확도 테스트 (brute force vs exhaustive)"""

import pytest
from itertools import product
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import search_builds
from src.sw_core.scoring import score_build, calculate_stats
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


def test_exhaustive_vs_brute_force_small():
    """작은 샘플에서 exhaustive 모드가 brute force와 완전히 일치하는지 검증"""
    runes = []
    
    # 슬롯당 2개씩만 (총 조합: 2^6 = 64개)
    for slot in range(1, 7):
        for i in range(2):
            if slot == 2 or slot == 6:
                main_stat_id = 4  # ATK%
                main_value = 63
            elif slot == 4:
                main_stat_id = 10  # CD
                main_value = 80
            else:
                main_stat_id = 4  # ATK%
                main_value = 63
            
            set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
            
            # 첫 번째 룬은 CR 20, 두 번째는 CR 15
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
        score, stats = score_build(combo_list, target="B", require_cr_100=True, require_sets=True)
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
        target="B",
        mode="exhaustive",
        top_n=1000,  # 모든 결과 요청
        require_sets=True
    )
    
    # 결과 개수가 정확히 일치해야 함
    assert len(exhaustive_results) == len(brute_force_results), \
        f"Exhaustive found {len(exhaustive_results)} but brute force found {len(brute_force_results)}"
    
    # 최고 점수가 일치해야 함
    if len(brute_force_results) > 0:
        assert exhaustive_results[0]["score"] == brute_force_results[0]["score"]
        
        # 모든 결과의 점수가 일치해야 함
        for i, (exh, bf) in enumerate(zip(exhaustive_results, brute_force_results)):
            assert exh["score"] == bf["score"], \
                f"Result {i}: exhaustive score {exh['score']} != brute force score {bf['score']}"


def test_exhaustive_with_constraints():
    """제약조건이 있을 때 exhaustive 모드가 모든 조건 만족 빌드를 찾는지 검증"""
    runes = []
    
    # 슬롯당 2개씩
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
            
            # 첫 번째 룬은 CR 20, 두 번째는 CR 15
            cr_value = 20 if i == 0 else 15
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # Brute force로 CR >= 100 조건 만족하는 모든 조합 찾기
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = [r for r in runes if r.slot == slot]
    
    brute_force_results = []
    for combo in product(*[slot_runes[i] for i in range(1, 7)]):
        combo_list = list(combo)
        score, stats = score_build(combo_list, target="B", require_cr_100=False, require_sets=True)
        if score > 0 and stats["cr_total"] >= 100:
            brute_force_results.append({
                "runes": combo_list,
                "score": score,
                "stats": stats
            })
    
    # 정렬
    brute_force_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Exhaustive 모드로 제약조건 검색
    exhaustive_results = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        constraints={"CR": 100},
        top_n=1000,
        require_sets=True
    )
    
    # 결과 개수가 정확히 일치해야 함
    assert len(exhaustive_results) == len(brute_force_results), \
        f"Exhaustive found {len(exhaustive_results)} but brute force found {len(brute_force_results)}"
    
    # 모든 결과가 CR >= 100을 만족해야 함
    for result in exhaustive_results:
        assert result["cr_total"] >= 100, f"CR constraint not satisfied: {result['cr_total']}"


def test_exhaustive_with_multiple_constraints():
    """여러 제약조건이 있을 때 exhaustive 모드가 모든 조건 만족 빌드를 찾는지 검증"""
    runes = []
    
    # 슬롯당 2개씩
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
            
            # 첫 번째 룬은 CR 20, SPD 10, 두 번째는 CR 15, SPD 5
            cr_value = 20 if i == 0 else 15
            spd_value = 10 if i == 0 else 5
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0), SubStat(8, spd_value, False, 0)]
            )
            runes.append(rune)
    
    # Brute force로 CR >= 100 AND SPD >= 50 조건 만족하는 모든 조합 찾기
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = [r for r in runes if r.slot == slot]
    
    brute_force_results = []
    base_spd = 104
    for combo in product(*[slot_runes[i] for i in range(1, 7)]):
        combo_list = list(combo)
        score, stats = score_build(combo_list, target="B", require_cr_100=False, require_sets=True)
        if score > 0:
            spd_total = base_spd + stats["spd_total"]
            if stats["cr_total"] >= 100 and spd_total >= 50:
                brute_force_results.append({
                    "runes": combo_list,
                    "score": score,
                    "stats": stats
                })
    
    # 정렬
    brute_force_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Exhaustive 모드로 제약조건 검색
    exhaustive_results = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        constraints={"CR": 100, "SPD": 50},
        top_n=1000,
        require_sets=True,
        base_spd=104
    )
    
    # 결과 개수가 정확히 일치해야 함
    assert len(exhaustive_results) == len(brute_force_results), \
        f"Exhaustive found {len(exhaustive_results)} but brute force found {len(brute_force_results)}"
    
    # 모든 결과가 제약조건을 만족해야 함
    for result in exhaustive_results:
        assert result["cr_total"] >= 100, f"CR constraint not satisfied: {result['cr_total']}"
        assert result["spd_total"] >= 50, f"SPD constraint not satisfied: {result['spd_total']}"


def test_exhaustive_return_all():
    """return_all=True일 때 모든 조건 만족 빌드를 반환하는지 검증"""
    runes = []
    
    # 슬롯당 2개씩
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
    
    # Brute force로 모든 유효한 조합 찾기
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = [r for r in runes if r.slot == slot]
    
    brute_force_results = []
    for combo in product(*[slot_runes[i] for i in range(1, 7)]):
        combo_list = list(combo)
        score, stats = score_build(combo_list, target="B", require_cr_100=True, require_sets=True)
        if score > 0:
            brute_force_results.append({
                "runes": combo_list,
                "score": score,
                "stats": stats
            })
    
    # Exhaustive 모드로 return_all=True 검색
    exhaustive_results = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        return_all=True,
        require_sets=True
    )
    
    # 결과 개수가 정확히 일치해야 함
    assert len(exhaustive_results) == len(brute_force_results), \
        f"Exhaustive found {len(exhaustive_results)} but brute force found {len(brute_force_results)}"


def test_exhaustive_objective_sorting():
    """objective에 따른 정렬이 올바른지 검증"""
    runes = []
    
    # 슬롯당 1개씩 (조합 1개만)
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
    
    # ATK_TOTAL 기준 정렬
    results = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        objective="ATK_TOTAL",
        top_n=10,
        require_sets=True
    )
    
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i]["atk_total"] >= results[i + 1]["atk_total"], \
                f"ATK_TOTAL not sorted: {results[i]['atk_total']} < {results[i + 1]['atk_total']}"

