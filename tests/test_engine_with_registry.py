"""엔진과 레지스트리 연동 테스트"""

import pytest
from src.sw_core.types import Rune, SubStat
from src.sw_core.api import run_search
from src.sw_core.monster_registry import MonsterRegistry
from src.sw_core.swex_parser import parse_swex_json


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
        quality=5,
        prefix_stat_id=0,
        prefix_stat_value=0.0
    )


@pytest.fixture
def sample_runes():
    """샘플 룬 리스트"""
    runes = []
    
    # Fatal 4 + Blade 2 조합
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
            [SubStat(9, 20, False, 0)]  # CR +20
        )
        runes.append(rune)
    
    return runes


def test_run_search_with_monster_master_id(sample_runes):
    """master_id로 몬스터 조회하여 탐색"""
    # 레지스트리 초기화 (CSV에서 로드)
    registry = MonsterRegistry(data_dirs=["data"])
    registry.warm_cache()
    
    # 루쉔으로 탐색
    result = run_search(
        runes=sample_runes,
        monster={"master_id": 14105},  # 루쉔
        constraints={"CR": 100},
        objective="SCORE",
        top_n=10,
        registry=registry
    )
    
    assert result is not None
    assert "results" in result
    # 레지스트리에서 조회된 base_atk=900, base_spd=110 사용됨


def test_run_search_with_monster_name(sample_runes):
    """이름으로 몬스터 조회하여 탐색"""
    registry = MonsterRegistry(data_dirs=["data"])
    registry.warm_cache()
    
    result = run_search(
        runes=sample_runes,
        monster={"name": "Lushen"},
        constraints={"CR": 100},
        objective="SCORE",
        top_n=10,
        registry=registry
    )
    
    assert result is not None
    assert "results" in result


def test_run_search_legacy_compatibility(sample_runes):
    """레거시 호환성: base_* 직접 지정"""
    result = run_search(
        runes=sample_runes,
        base_atk=900,
        base_spd=104,
        constraints={"CR": 100},
        objective="SCORE",
        top_n=10
    )
    
    assert result is not None
    assert "results" in result


def test_run_search_default_stats(sample_runes):
    """monster 미지정 시 기본값 사용"""
    result = run_search(
        runes=sample_runes,
        constraints={"CR": 100},
        objective="SCORE",
        top_n=10
    )
    
    assert result is not None
    assert "results" in result
    # 기본값 사용 (base_atk=900, base_spd=104 등)

