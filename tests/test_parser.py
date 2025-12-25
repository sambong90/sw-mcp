"""파서 테스트"""

import json
import pytest
from src.sw_mcp.swex_parser import parse_rune, parse_swex_json
from src.sw_mcp.types import Rune


def test_parse_rune_intangible():
    """무형 룬 파싱 테스트 (set_id=25)"""
    raw_rune = {
        "rune_id": 12345,
        "slot_no": 1,
        "set_id": 25,  # Intangible
        "pri_eff": [4, 63],  # ATK% 63
        "sec_eff": [
            [9, 5, 0, 0],  # CR 5
            [10, 7, 0, 0],  # CD 7
        ],
        "class": 6,
        "rank": 5
    }
    
    rune = parse_rune(raw_rune)
    assert rune is not None
    assert rune.rune_id == 12345
    assert rune.set_id == 25
    assert rune.intangible is True
    assert rune.set_name == "Intangible"


def test_parse_rune_with_grind():
    """연마가 포함된 룬 파싱 테스트"""
    raw_rune = {
        "rune_id": 12346,
        "slot_no": 2,
        "set_id": 8,  # Fatal
        "pri_eff": [4, 63],  # ATK% 63
        "sec_eff": [
            [9, 5, 0, 3],  # CR 5 + grind 3 = 8
            [10, 7, 1, 5],  # CD 7 + grind 5 = 12 (enchanted)
        ],
        "class": 6,
        "rank": 5
    }
    
    rune = parse_rune(raw_rune)
    assert rune is not None
    assert len(rune.subs) == 2
    
    cr_sub = rune.get_sub_stat(9)
    assert cr_sub is not None
    assert cr_sub.value == 8.0  # 5 + 3
    assert cr_sub.grind == 3.0
    
    cd_sub = rune.get_sub_stat(10)
    assert cd_sub is not None
    assert cd_sub.value == 12.0  # 7 + 5
    assert cd_sub.enchanted is True


def test_parse_swex_json_merge():
    """rune_list와 unit_list 병합 테스트"""
    json_data = {
        "runes": [
            {
                "rune_id": 100,
                "slot_no": 1,
                "set_id": 5,  # Rage
                "pri_eff": [4, 63],
                "sec_eff": [],
                "class": 6,
                "rank": 5
            }
        ],
        "unit_list": [  # unit_list 우선 확인
            {
                "runes": [
                    {
                        "rune_id": 200,
                        "slot_no": 2,
                        "set_id": 4,  # Blade
                        "pri_eff": [4, 63],
                        "sec_eff": [],
                        "class": 6,
                        "rank": 5
                    },
                    {
                        "rune_id": 100,  # 중복 (rune_list에도 있음)
                        "slot_no": 1,
                        "set_id": 5,
                        "pri_eff": [4, 63],
                        "sec_eff": [],
                        "class": 6,
                        "rank": 5
                    }
                ]
            }
        ],
        "units": [  # units도 확인
            {
                "runes": [
                    {
                        "rune_id": 300,
                        "slot_no": 3,
                        "set_id": 5,
                        "pri_eff": [4, 63],
                        "sec_eff": [],
                        "class": 6,
                        "rank": 5
                    }
                ]
            }
        ]
    }
    
    runes = parse_swex_json(json_data)
    rune_ids = [r.rune_id for r in runes]
    
    # 중복 제거 확인 및 unit_list 읽기 확인
    assert len(runes) == 3
    assert 100 in rune_ids
    assert 200 in rune_ids
    assert 300 in rune_ids
    assert rune_ids.count(100) == 1  # 중복 없음


def test_parse_rune_prefix_eff():
    """prefix_eff 파싱 테스트"""
    raw_rune = {
        "rune_id": 12347,
        "slot_no": 1,
        "set_id": 5,
        "pri_eff": [4, 63],
        "prefix_eff": [9, 5],  # CR 5
        "sec_eff": [],
        "class": 6,
        "rank": 5
    }
    
    rune = parse_rune(raw_rune)
    assert rune is not None
    assert rune.has_prefix is True
    assert rune.prefix_stat_id == 9
    assert rune.prefix_stat_value == 5.0
    assert rune.prefix_stat_name == "CR"
    
    # prefix_eff가 0인 경우
    raw_rune2 = {
        "rune_id": 12348,
        "slot_no": 2,
        "set_id": 5,
        "pri_eff": [4, 63],
        "prefix_eff": 0,
        "sec_eff": [],
        "class": 6,
        "rank": 5
    }
    
    rune2 = parse_rune(raw_rune2)
    assert rune2 is not None
    assert rune2.has_prefix is False
    assert rune2.prefix_stat_id == 0

