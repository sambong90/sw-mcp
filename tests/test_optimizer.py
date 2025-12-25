"""최적화 테스트"""

import pytest
from src.sw_mcp.types import Rune, SubStat
from src.sw_mcp.optimizer import optimize_lushen, filter_rune_by_slot


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


def test_slot3_atk_percent_exclusion():
    """슬롯3에 ATK% 서브옵이 있는 룬은 제외되는지 테스트"""
    runes = [
        create_test_rune(1, 3, 5, 4, 63, [SubStat(4, 10, False, 0)]),  # ATK% 서브옵 있음
        create_test_rune(2, 3, 5, 4, 63, [SubStat(9, 10, False, 0)]),  # CR 서브옵만 있음
    ]
    
    filtered = filter_rune_by_slot(runes, 3, "B")
    
    # ATK% 서브옵이 있는 룬은 제외되어야 함
    assert len(filtered) == 1
    assert filtered[0].rune_id == 2


def test_slot_requirements():
    """슬롯별 메인 스탯 요구사항 테스트"""
    # 슬롯2: ATK%만 허용
    runes_slot2 = [
        create_test_rune(1, 2, 5, 4, 63),  # ATK% - OK
        create_test_rune(2, 2, 5, 9, 58),  # CR - 제외
    ]
    filtered = filter_rune_by_slot(runes_slot2, 2, "B")
    assert len(filtered) == 1
    assert filtered[0].rune_id == 1
    
    # 슬롯4: CD만 허용
    runes_slot4 = [
        create_test_rune(3, 4, 5, 10, 80),  # CD - OK
        create_test_rune(4, 4, 5, 4, 63),   # ATK% - 제외
    ]
    filtered = filter_rune_by_slot(runes_slot4, 4, "B")
    assert len(filtered) == 1
    assert filtered[0].rune_id == 3
    
    # 슬롯6: ATK%만 허용
    runes_slot6 = [
        create_test_rune(5, 6, 5, 4, 63),  # ATK% - OK
        create_test_rune(6, 6, 5, 6, 63),   # DEF% - 제외
    ]
    filtered = filter_rune_by_slot(runes_slot6, 6, "B")
    assert len(filtered) == 1
    assert filtered[0].rune_id == 5


def test_optimize_lushen_basic():
    """기본 최적화 테스트"""
    # 최소한의 룬 세트 구성
    runes = []
    
    # 슬롯별 룬 생성
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
    
    # 결과가 있어야 함
    assert len(results) > 0
    
    # 최고 점수가 0보다 커야 함
    if results:
        assert results[0]["score"] > 0
        assert results[0]["cr_total"] >= 100.0  # 치확 조건 만족

