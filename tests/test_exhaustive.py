"""Exhaustive search ?�스??""

import pytest
from itertools import product
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import optimize_lushen, search_builds
from src.sw_core.scoring import score_build


def create_test_rune(rune_id, slot, set_id, main_stat_id, main_value, subs=None, prefix_stat_id=0, prefix_stat_value=0.0):
    """?�스?�용 �??�성"""
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
    """target A가 Fatal 4 + Blade 2�?거�??�는지 ?�스??""
    runes = []
    
    # Fatal 4�?+ Blade 2�??�성
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
        
        # Fatal 4�? Blade 2�?
        set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    # target="A"�?검??(Rage 4 + Blade 2 ?�요)
    results = optimize_lushen(runes, target="A", mode="exhaustive", top_n=10)
    
    # Fatal???�으므�?결과가 ?�어????
    assert len(results) == 0
    
    # search_builds???�스??
    results2 = search_builds(runes, target="A", mode="exhaustive", top_n=10)
    assert len(results2) == 0


def test_exhaustive_matches_brute_force():
    """exhaustive 모드가 brute force?� ?�치?�는지 ?�스??(?��? fixture)"""
    # 매우 ?��? fixture: ?�롯??2개씩�?
    runes = []
    
    for slot in range(1, 7):
        for i in range(2):  # ?�롯??2�?
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
            
            # �?번째 룬�? CR 20, ??번째??CR 15
            cr_value = 20 if i == 0 else 15
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # exhaustive 모드�?검??
    results_exhaustive = optimize_lushen(
        runes, target="A", mode="exhaustive", top_n=100
    )
    
    # brute force�?모든 조합 검??
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
    
    # ?�렬
    brute_force_results.sort(key=lambda x: x["score"], reverse=True)
    results_exhaustive_sorted = sorted(results_exhaustive, key=lambda x: x["score"], reverse=True)
    
    # 결과 개수가 ?�치?�야 ??
    assert len(results_exhaustive) == len(brute_force_results)
    
    # 최고 ?�수가 ?�치?�야 ??
    if len(brute_force_results) > 0:
        assert results_exhaustive_sorted[0]["score"] == brute_force_results[0]["score"]


def test_all_at_best_returns_ties():
    """all_at_best가 tie�?모두 반환?�는지 ?�스??""
    runes = []
    
    # ?�일???�탯??가�?룬들 ?�성 (tie 발생)
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
        
        # ?�롯??2개씩 ?�성 (?�일???�탯)
        for i in range(2):
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, 20, False, 0)]
            )
            runes.append(rune)
    
    # all_at_best�?검??
    results = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        objective="SCORE",
        return_policy="all_at_best",
        top_n=100
    )
    
    # 최고 ?�수가 모두 같아????
    if len(results) > 1:
        best_score = results[0]["score"]
        for result in results:
            assert result["score"] == best_score


def test_require_sets_false_allows_any_sets():
    """require_sets=False????모든 ?�트가 ?�용?�는지 ?�스??""
    runes = []
    
    # ?�양???�트??�??�성 (Rage/Fatal/Blade 조건 불만�?
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
        
        # Swift 3�? Violent 3�?(?�트 조건 불만�?
        set_id = 3 if slot <= 3 else 13  # Swift 3 + Violent 3
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    # require_sets=True�?결과 ?�음
    results_with_sets = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=True,
        constraints={"CR": 100}
    )
    assert len(results_with_sets) == 0
    
    # require_sets=False�?결과 ?�음 (CR>=100�?체크)
    results_no_sets = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=False,
        constraints={"CR": 100}
    )
    # CR 조건??만족?�면 결과가 ?�어????
    assert len(results_no_sets) > 0


def test_cr_100_not_hardcoded():
    """CR>=100??hardcode?��? ?�고 constraints?�만 ?�존?�는지 ?�스??""
    runes = []
    
    # CR < 100??�??�성
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
            [SubStat(9, 5, False, 0)]  # CR 5�?(�?CR < 100)
        )
        runes.append(rune)
    
    # constraints??CR???�으�?결과 ?�음 (기본 require_cr_100=True)
    results_no_cr_constraint = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        constraints={}  # CR 조건 ?�음
    )
    assert len(results_no_cr_constraint) == 0
    
    # constraints??CR=50?�면 결과 ?�음 (CR>=50�?체크)
    results_with_cr_constraint = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        constraints={"CR": 50}  # CR>=50�?체크
    )
    # CR>=50?�면 결과가 ?�어????
    assert len(results_with_cr_constraint) > 0

