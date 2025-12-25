"""search_builds 테스트"""

import pytest
from src.sw_mcp.types import Rune, SubStat
from src.sw_mcp.optimizer import search_builds


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


def test_search_builds_with_constraints():
    """제약 조건으로 필터링되는지 테스트"""
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
    
    # 제약 조건: CR >= 100, CD >= 150
    constraints = {
        "CR": 100.0,
        "CD": 150.0
    }
    
    results = search_builds(
        runes=runes,
        target="B",
        constraints=constraints,
        top_n=10
    )
    
    # 결과가 있으면 모든 결과가 제약 조건을 만족해야 함
    for result in results:
        assert result["cr_total"] >= 100.0
        assert result["cd_total"] >= 150.0


def test_search_builds_objective():
    """objective에 따라 정렬되는지 테스트"""
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
    
    # ATK_TOTAL 기준으로 정렬
    results = search_builds(
        runes=runes,
        target="B",
        objective="ATK_TOTAL",
        top_n=5
    )
    
    # 내림차순으로 정렬되어야 함
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i]["atk_total"] >= results[i + 1]["atk_total"]


def test_search_builds_min_score():
    """MIN_SCORE 제약 조건 테스트"""
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
    
    constraints = {
        "MIN_SCORE": 4000.0
    }
    
    results = search_builds(
        runes=runes,
        target="B",
        constraints=constraints,
        top_n=10
    )
    
    # 모든 결과가 MIN_SCORE 이상이어야 함
    for result in results:
        assert result["score"] >= 4000.0

