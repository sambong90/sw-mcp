"""Exhaustive search ?ŒìŠ¤??""

import pytest
from itertools import product
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import optimize_lushen, search_builds
from src.sw_core.scoring import score_build


def create_test_rune(rune_id, slot, set_id, main_stat_id, main_value, subs=None, prefix_stat_id=0, prefix_stat_value=0.0):
    """?ŒìŠ¤?¸ìš© ë£??ì„±"""
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
    """target Aê°€ Fatal 4 + Blade 2ë¥?ê±°ë??˜ëŠ”ì§€ ?ŒìŠ¤??""
    runes = []
    
    # Fatal 4ê°?+ Blade 2ê°??ì„±
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
        
        # Fatal 4ê°? Blade 2ê°?
        set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    # target="A"ë¡?ê²€??(Rage 4 + Blade 2 ?„ìš”)
    results = optimize_lushen(runes, target="A", mode="exhaustive", top_n=10)
    
    # Fatal???ˆìœ¼ë¯€ë¡?ê²°ê³¼ê°€ ?†ì–´????
    assert len(results) == 0
    
    # search_builds???ŒìŠ¤??
    results2 = search_builds(runes, target="A", mode="exhaustive", top_n=10)
    assert len(results2) == 0


def test_exhaustive_matches_brute_force():
    """exhaustive ëª¨ë“œê°€ brute force?€ ?¼ì¹˜?˜ëŠ”ì§€ ?ŒìŠ¤??(?‘ì? fixture)"""
    # ë§¤ìš° ?‘ì? fixture: ?¬ë¡¯??2ê°œì”©ë§?
    runes = []
    
    for slot in range(1, 7):
        for i in range(2):  # ?¬ë¡¯??2ê°?
            if slot == 2 or slot == 6:
                main_stat_id = 4
                main_value = 63
            elif slot == 4:
                main_stat_id = 10
                main_value = 80
            else:
                main_stat_id = 4
                main_value = 63
            
            # Rage 4 + Blade 2 êµ¬ì„±
            if slot <= 4:
                set_id = 5  # Rage
            else:
                set_id = 4  # Blade
            
            # ì²?ë²ˆì§¸ ë£¬ì? CR 20, ??ë²ˆì§¸??CR 15
            cr_value = 20 if i == 0 else 15
            
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, cr_value, False, 0)]
            )
            runes.append(rune)
    
    # exhaustive ëª¨ë“œë¡?ê²€??
    results_exhaustive = optimize_lushen(
        runes, target="A", mode="exhaustive", top_n=100
    )
    
    # brute forceë¡?ëª¨ë“  ì¡°í•© ê²€??
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
    
    # ?•ë ¬
    brute_force_results.sort(key=lambda x: x["score"], reverse=True)
    results_exhaustive_sorted = sorted(results_exhaustive, key=lambda x: x["score"], reverse=True)
    
    # ê²°ê³¼ ê°œìˆ˜ê°€ ?¼ì¹˜?´ì•¼ ??
    assert len(results_exhaustive) == len(brute_force_results)
    
    # ìµœê³  ?ìˆ˜ê°€ ?¼ì¹˜?´ì•¼ ??
    if len(brute_force_results) > 0:
        assert results_exhaustive_sorted[0]["score"] == brute_force_results[0]["score"]


def test_all_at_best_returns_ties():
    """all_at_bestê°€ tieë¥?ëª¨ë‘ ë°˜í™˜?˜ëŠ”ì§€ ?ŒìŠ¤??""
    runes = []
    
    # ?™ì¼???¤íƒ¯??ê°€ì§?ë£¬ë“¤ ?ì„± (tie ë°œìƒ)
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
        
        # ?¬ë¡¯??2ê°œì”© ?ì„± (?™ì¼???¤íƒ¯)
        for i in range(2):
            rune = create_test_rune(
                slot * 100 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, 20, False, 0)]
            )
            runes.append(rune)
    
    # all_at_bestë¡?ê²€??
    results = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        objective="SCORE",
        return_policy="all_at_best",
        top_n=100
    )
    
    # ìµœê³  ?ìˆ˜ê°€ ëª¨ë‘ ê°™ì•„????
    if len(results) > 1:
        best_score = results[0]["score"]
        for result in results:
            assert result["score"] == best_score


def test_require_sets_false_allows_any_sets():
    """require_sets=False????ëª¨ë“  ?¸íŠ¸ê°€ ?ˆìš©?˜ëŠ”ì§€ ?ŒìŠ¤??""
    runes = []
    
    # ?¤ì–‘???¸íŠ¸??ë£??ì„± (Rage/Fatal/Blade ì¡°ê±´ ë¶ˆë§Œì¡?
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
        
        # Swift 3ê°? Violent 3ê°?(?¸íŠ¸ ì¡°ê±´ ë¶ˆë§Œì¡?
        set_id = 3 if slot <= 3 else 13  # Swift 3 + Violent 3
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    # require_sets=Trueë©?ê²°ê³¼ ?†ìŒ
    results_with_sets = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=True,
        constraints={"CR": 100}
    )
    assert len(results_with_sets) == 0
    
    # require_sets=Falseë©?ê²°ê³¼ ?ˆìŒ (CR>=100ë§?ì²´í¬)
    results_no_sets = search_builds(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=False,
        constraints={"CR": 100}
    )
    # CR ì¡°ê±´??ë§Œì¡±?˜ë©´ ê²°ê³¼ê°€ ?ˆì–´????
    assert len(results_no_sets) > 0


def test_cr_100_not_hardcoded():
    """CR>=100??hardcode?˜ì? ?Šê³  constraints?ë§Œ ?˜ì¡´?˜ëŠ”ì§€ ?ŒìŠ¤??""
    runes = []
    
    # CR < 100??ë£??ì„±
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
            [SubStat(9, 5, False, 0)]  # CR 5ë§?(ì´?CR < 100)
        )
        runes.append(rune)
    
    # constraints??CR???†ìœ¼ë©?ê²°ê³¼ ?†ìŒ (ê¸°ë³¸ require_cr_100=True)
    results_no_cr_constraint = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        constraints={}  # CR ì¡°ê±´ ?†ìŒ
    )
    assert len(results_no_cr_constraint) == 0
    
    # constraints??CR=50?´ë©´ ê²°ê³¼ ?ˆìŒ (CR>=50ë§?ì²´í¬)
    results_with_cr_constraint = search_builds(
        runes=runes,
        target="A",
        mode="exhaustive",
        constraints={"CR": 50}  # CR>=50ë§?ì²´í¬
    )
    # CR>=50?´ë©´ ê²°ê³¼ê°€ ?ˆì–´????
    assert len(results_with_cr_constraint) > 0

