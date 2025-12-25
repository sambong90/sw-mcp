"""API ?ŒìŠ¤??""

import pytest
from src.sw_core.api import run_search, run_search_from_json
from src.sw_core.types import Rune, SubStat


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


def test_run_search_basic():
    """ê¸°ë³¸ run_search ?ŒìŠ¤??""
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
        
        set_id = 5 if slot <= 4 else 4  # Rage 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    result = run_search(
        runes=runes,
        target="A",
        mode="exhaustive",
        top_n=10
    )
    
    assert "results" in result
    assert "total_found" in result
    assert "search_params" in result
    assert "mode" in result
    assert result["mode"] == "exhaustive"
    assert isinstance(result["results"], list)


def test_run_search_with_constraints():
    """?œì•½ ì¡°ê±´???ˆëŠ” run_search ?ŒìŠ¤??""
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
    
    result = run_search(
        runes=runes,
        target="B",
        mode="exhaustive",
        constraints={"CR": 100, "CD": 150},
        objective="SCORE",
        top_n=10
    )
    
    assert result["total_found"] > 0
    for build in result["results"]:
        assert build["cr_total"] >= 100
        assert build["cd_total"] >= 150


def test_run_search_exhaustive_vs_fast():
    """Exhaustive ëª¨ë“œê°€ fast ëª¨ë“œë³´ë‹¤ ??ë§ì? ê²°ê³¼ë¥?ì°¾ëŠ”ì§€ ?ŒìŠ¤??""
    runes = []
    
    # ?¬ë¡¯???¬ëŸ¬ ë£??ì„±
    for slot in range(1, 7):
        for i in range(3):  # ?¬ë¡¯??3ê°?
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
                slot * 1000 + i, slot, set_id, main_stat_id, main_value,
                [SubStat(9, 20, False, 0)]
            )
            runes.append(rune)
    
    result_exhaustive = run_search(
        runes=runes,
        target="B",
        mode="exhaustive",
        top_n=100
    )
    
    result_fast = run_search(
        runes=runes,
        target="B",
        mode="fast",
        max_candidates_per_slot=50,
        top_n=100
    )
    
    # Exhaustiveê°€ fastë³´ë‹¤ ê°™ê±°????ë§ì? ê²°ê³¼ë¥?ì°¾ì•„????
    assert result_exhaustive["total_found"] >= result_fast["total_found"]


def test_run_search_from_json():
    """run_search_from_json ?ŒìŠ¤??""
    json_data = {
        "runes": [
            {
                "rune_id": 100,
                "slot_no": 1,
                "set_id": 5,  # Rage
                "pri_eff": [4, 63],  # ATK%
                "sec_eff": [[9, 20, 0, 0]],  # CR 20
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            }
        ],
        "unit_list": []
    }
    
    result = run_search_from_json(
        json_data=json_data,
        target="A",
        mode="exhaustive",
        top_n=10
    )
    
    assert "results" in result
    assert "total_found" in result


def test_run_search_objective_sorting():
    """Objective???°ë¥¸ ?•ë ¬ ?ŒìŠ¤??""
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
        
        set_id = 8 if slot <= 4 else 4
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    # ATK_TOTAL ê¸°ì? ?•ë ¬
    result = run_search(
        runes=runes,
        target="B",
        mode="exhaustive",
        objective="ATK_TOTAL",
        top_n=10
    )
    
    if len(result["results"]) > 1:
        for i in range(len(result["results"]) - 1):
            assert result["results"][i]["atk_total"] >= result["results"][i + 1]["atk_total"]


def test_run_search_require_sets_false():
    """require_sets=False ?ŒìŠ¤??""
    runes = []
    
    # ?¤ì–‘???¸íŠ¸??ë£??ì„± (?¸íŠ¸ ì¡°ê±´ ë¶ˆë§Œì¡?
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
        
        set_id = 3 if slot <= 3 else 13  # Swift 3 + Violent 3
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    # require_sets=Falseë©?ê²°ê³¼ê°€ ?ˆì–´????
    result = run_search(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=False,
        constraints={"CR": 100}
    )
    
    assert result["total_found"] > 0

