"""최적???�스??""

import pytest
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import optimize_lushen, filter_rune_by_slot


def create_test_rune(rune_id, slot, set_id, main_stat_id, main_value, subs=None):
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
        quality=5
    )


def test_slot3_atk_percent_exclusion():
    """?�롯3??ATK% ?�브?�이 ?�는 룬�? ?�외?�는지 ?�스??""
    runes = [
        create_test_rune(1, 3, 5, 4, 63, [SubStat(4, 10, False, 0)]),  # ATK% ?�브???�음
        create_test_rune(2, 3, 5, 4, 63, [SubStat(9, 10, False, 0)]),  # CR ?�브?�만 ?�음
    ]
    
    filtered = filter_rune_by_slot(runes, 3, "B")
    
    # ATK% ?�브?�이 ?�는 룬�? ?�외?�어????
    assert len(filtered) == 1
    assert filtered[0].rune_id == 2


def test_slot_requirements():
    """?�롯�?메인 ?�탯 ?�구?�항 ?�스??""
    # ?�롯2: ATK%�??�용
    runes_slot2 = [
        create_test_rune(1, 2, 5, 4, 63),  # ATK% - OK
        create_test_rune(2, 2, 5, 9, 58),  # CR - ?�외
    ]
    filtered = filter_rune_by_slot(runes_slot2, 2, "B")
    assert len(filtered) == 1
    assert filtered[0].rune_id == 1
    
    # ?�롯4: CD�??�용
    runes_slot4 = [
        create_test_rune(3, 4, 5, 10, 80),  # CD - OK
        create_test_rune(4, 4, 5, 4, 63),   # ATK% - ?�외
    ]
    filtered = filter_rune_by_slot(runes_slot4, 4, "B")
    assert len(filtered) == 1
    assert filtered[0].rune_id == 3
    
    # ?�롯6: ATK%�??�용
    runes_slot6 = [
        create_test_rune(5, 6, 5, 4, 63),  # ATK% - OK
        create_test_rune(6, 6, 5, 6, 63),   # DEF% - ?�외
    ]
    filtered = filter_rune_by_slot(runes_slot6, 6, "B")
    assert len(filtered) == 1
    assert filtered[0].rune_id == 5


def test_optimize_lushen_basic():
    """기본 최적???�스??""
    # 최소?�의 �??�트 구성
    runes = []
    
    # ?�롯�?�??�성
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
        
        set_id = 8 if slot <= 4 else 4  # Fatal 4 + Blade 2
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]  # CR 20
        )
        runes.append(rune)
    
    results = optimize_lushen(runes, target="B", top_n=5)
    
    # 결과가 ?�어????
    assert len(results) > 0
    
    # 최고 ?�수가 0보다 커야 ??
    if results:
        assert results[0]["score"] > 0
        assert results[0]["cr_total"] >= 100.0  # 치확 조건 만족

