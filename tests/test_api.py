"""API ?�스??""

import pytest
from src.sw_core.api import run_search, run_search_from_json
from src.sw_core.types import Rune, SubStat


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


def test_run_search_basic():
    """기본 run_search ?�스??""
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
    """?�약 조건???�는 run_search ?�스??""
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
    """Exhaustive 모드가 fast 모드보다 ??많�? 결과�?찾는지 ?�스??""
    runes = []
    
    # ?�롯???�러 �??�성
    for slot in range(1, 7):
        for i in range(3):  # ?�롯??3�?
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
    
    # Exhaustive가 fast보다 같거????많�? 결과�?찾아????
    assert result_exhaustive["total_found"] >= result_fast["total_found"]


def test_run_search_from_json():
    """run_search_from_json ?�스??""
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
    """Objective???�른 ?�렬 ?�스??""
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
    
    # ATK_TOTAL 기�? ?�렬
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
    """require_sets=False ?�스??""
    runes = []
    
    # ?�양???�트??�??�성 (?�트 조건 불만�?
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
    
    # require_sets=False�?결과가 ?�어????
    result = run_search(
        runes=runes,
        target="B",
        mode="exhaustive",
        require_sets=False,
        constraints={"CR": 100}
    )
    
    assert result["total_found"] > 0


