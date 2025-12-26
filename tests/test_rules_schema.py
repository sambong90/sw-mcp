"""Test ruleset schema validation"""

import pytest
import json
from src.sw_mcp.rules.schema import Ruleset, Metadata, Source, RuneRules, SetRules, SetBonus


def test_ruleset_schema_validation():
    """Test that ruleset schema validates correctly"""
    ruleset = Ruleset(
        version="v1.0.0",
        metadata=Metadata(
            effective_date="2024-01-01",
            patch_version="7.0.0",
            sources=[Source(type="test", notes="Test")],
            confidence="high"
        ),
        rune_rules=RuneRules(
            slot_main_disallowed={2: [10, 9]},
            sub_no_dup_main=True
        ),
        set_rules=SetRules(
            sets={1: SetBonus(set_id=1, set_name="Energy", bonus_2={"HP_PCT": 15.0})}
        ),
        gem_grind_rules=GemGrindRules(),
        substats_rules=SubstatsRules(),
        content_rules=ContentRules(),
    )
    
    # Should serialize/deserialize
    json_str = ruleset.model_dump_json()
    data = json.loads(json_str)
    ruleset2 = Ruleset(**data)
    
    assert ruleset2.version == "v1.0.0"
    assert ruleset2.rune_rules.slot_main_disallowed[2] == [10, 9]


def test_ruleset_from_json():
    """Test loading ruleset from JSON"""
    json_data = {
        "version": "v1.0.0",
        "metadata": {
            "effective_date": "2024-01-01",
            "patch_version": "7.0.0",
            "sources": [{"type": "test"}],
            "confidence": "high"
        },
        "rune_rules": {
            "slot_main_disallowed": {"2": [10, 9]},
            "sub_no_dup_main": True
        },
        "set_rules": {
            "sets": {
                "1": {
                    "set_id": 1,
                    "set_name": "Energy",
                    "bonus_2": {"HP_PCT": 15.0}
                }
            }
        },
        "gem_grind_rules": {
            "gem_allowed_stats": [1, 2, 3],
            "grind_allowed_stats": [1, 2, 3],
            "caps": []
        },
        "substats_rules": {
            "ranges": []
        },
        "content_rules": {
            "contents": []
        }
    }
    
    ruleset = Ruleset(**json_data)
    assert ruleset.version == "v1.0.0"
    assert len(ruleset.set_rules.sets) == 1

