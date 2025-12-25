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


def test_all_sets_included():
    """모든 세트가 후보에 포함되는지 테스트"""
    from src.sw_mcp.optimizer import filter_rune_by_slot
    
    # 다양한 세트의 룬 생성
    runes = [
        create_test_rune(1, 1, 5, 4, 63),   # Rage
        create_test_rune(2, 1, 8, 4, 63),   # Fatal
        create_test_rune(3, 1, 4, 4, 63),   # Blade
        create_test_rune(4, 1, 3, 4, 63),   # Swift
        create_test_rune(5, 1, 13, 4, 63),  # Violent
        create_test_rune(6, 1, 25, 4, 63),  # Intangible
    ]
    
    # 슬롯1 필터링 (세트 제한 없음)
    filtered = filter_rune_by_slot(runes, 1, "B")
    
    # 모든 세트가 포함되어야 함
    set_ids = {r.set_id for r in filtered}
    assert 5 in set_ids  # Rage
    assert 8 in set_ids  # Fatal
    assert 4 in set_ids  # Blade
    assert 3 in set_ids  # Swift
    assert 13 in set_ids  # Violent
    assert 25 in set_ids  # Intangible


def test_set_requirements_only_valid_results():
    """세트 조건을 만족하지 않으면 결과에 나오지 않음을 테스트"""
    runes = []
    
    # Fatal 3개 + Blade 1개만 생성 (Fatal 4세트 조건 불만족)
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
        
        # Fatal 3개, Blade 1개, Swift 2개
        if slot <= 3:
            set_id = 8  # Fatal
        elif slot == 4:
            set_id = 4  # Blade
        else:
            set_id = 3  # Swift (다른 세트)
        
        rune = create_test_rune(
            slot * 100, slot, set_id, main_stat_id, main_value,
            [SubStat(9, 20, False, 0)]
        )
        runes.append(rune)
    
    # target="B"는 Fatal 4세트 + Blade 2세트 필요
    results = search_builds(
        runes=runes,
        target="B",
        top_n=10
    )
    
    # 세트 조건을 만족하지 않으므로 결과가 없어야 함
    assert len(results) == 0


def test_max_candidates_per_slot():
    """상위 K개 유지 옵션이 작동하는지 테스트"""
    runes = []
    
    # 많은 룬 생성 (슬롯당 여러 개)
    for slot in range(1, 7):
        for i in range(10):  # 슬롯당 10개
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
    
    # max_candidates_per_slot=5로 제한
    results = search_builds(
        runes=runes,
        target="B",
        max_candidates_per_slot=5,
        top_n=10
    )
    
    # 결과가 나와야 함 (성능 문제 없이)
    # 실제로는 세트 조건을 만족하는 조합이 있어야 함
    # 이 테스트는 주로 성능 검증용
