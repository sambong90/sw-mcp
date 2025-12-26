"""Test rules engine"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.sw_mcp.rules.schema import Ruleset, Metadata, Source, RuneRules, SetRules, SetBonus, GemGrindRules, SubstatsRules, ContentRules
from src.sw_mcp.rules.engine import RulesEngine
from src.sw_core.types import Rune, SubStat


@pytest.fixture
def sample_ruleset():
    """Create sample ruleset"""
    return Ruleset(
        version="v1.0.0",
        metadata=Metadata(
            effective_date="2024-01-01",
            patch_version="7.0.0",
            sources=[Source(type="test", notes="Test ruleset")],
            confidence="high"
        ),
        rune_rules=RuneRules(
            slot_main_disallowed={
                2: [10, 9, 11, 12],  # CD, CR, RES, ACC
                4: [8, 11, 12],  # SPD, RES, ACC
                6: [8, 10, 9]  # SPD, CD, CR
            },
            sub_no_dup_main=True,
            slot_special_rules=[
                {
                    "slot": 1,
                    "disallowed_main": [5, 6],  # DEF%, DEF+
                    "disallowed_sub": [5, 6],
                    "disallowed_prefix": [5, 6]
                },
                {
                    "slot": 3,
                    "disallowed_main": [3, 4],  # ATK%, ATK+
                    "disallowed_sub": [3, 4],
                    "disallowed_prefix": [3, 4]
                }
            ]
        ),
        set_rules=SetRules(
            sets={
                2: SetBonus(set_id=2, set_name="Blade", bonus_2={"CR": 12.0}),
                8: SetBonus(set_id=8, set_name="Fatal", bonus_4={"ATK_PCT": 35.0}),
                10: SetBonus(set_id=10, set_name="Rage", bonus_4={"CD": 40.0}),
            }
        ),
        gem_grind_rules=GemGrindRules(
            gem_allowed_stats=[1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
            grind_allowed_stats=[1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
            caps=[]
        ),
        substats_rules=SubstatsRules(ranges=[]),
        content_rules=ContentRules(),
    )


def test_validate_rune_slot_main_disallowed(sample_ruleset):
    """Test slot main stat disallowed rule"""
    engine = RulesEngine(sample_ruleset)
    
    # Slot 2 cannot have CD (10)
    rune = Rune(
        rune_id=1, slot=2, set_id=1, main_stat_id=10, main_stat_value=50.0,
        subs=[], level=15, quality=6
    )
    is_valid, error = engine.validate_rune(rune)
    assert not is_valid
    assert "disallowed" in error.lower()


def test_validate_rune_slot_special_rule(sample_ruleset):
    """Test slot special rules"""
    engine = RulesEngine(sample_ruleset)
    
    # Slot 1 cannot have DEF% (6)
    rune = Rune(
        rune_id=1, slot=1, set_id=1, main_stat_id=6, main_stat_value=50.0,
        subs=[], level=15, quality=6
    )
    is_valid, error = engine.validate_rune(rune)
    assert not is_valid
    
    # Slot 3 cannot have ATK% (4)
    rune = Rune(
        rune_id=2, slot=3, set_id=1, main_stat_id=4, main_stat_value=50.0,
        subs=[], level=15, quality=6
    )
    is_valid, error = engine.validate_rune(rune)
    assert not is_valid


def test_validate_rune_sub_no_dup_main(sample_ruleset):
    """Test sub no dup main rule"""
    engine = RulesEngine(sample_ruleset)
    
    # Substat duplicates main stat
    rune = Rune(
        rune_id=1, slot=2, set_id=1, main_stat_id=4, main_stat_value=50.0,
        subs=[SubStat(stat_id=4, value=10.0)], level=15, quality=6
    )
    is_valid, error = engine.validate_rune(rune)
    assert not is_valid
    assert "duplicate" in error.lower()


def test_validate_build(sample_ruleset):
    """Test build validation"""
    engine = RulesEngine(sample_ruleset)
    
    # Valid 6-rune build
    runes = [
        Rune(rune_id=i, slot=i, set_id=1, main_stat_id=1, main_stat_value=100.0, subs=[], level=15, quality=6)
        for i in range(1, 7)
    ]
    is_valid, error = engine.validate_build(runes)
    assert is_valid
    
    # Invalid: duplicate slots
    runes[1].slot = 1
    is_valid, error = engine.validate_build(runes)
    assert not is_valid
    assert "duplicate" in error.lower()


def test_apply_set_bonus(sample_ruleset):
    """Test set bonus application"""
    engine = RulesEngine(sample_ruleset)
    
    # Blade 2-set: CR +12
    runes = [
        Rune(rune_id=1, slot=1, set_id=2, main_stat_id=1, main_stat_value=100.0, subs=[], level=15, quality=6),
        Rune(rune_id=2, slot=2, set_id=2, main_stat_id=1, main_stat_value=100.0, subs=[], level=15, quality=6),
    ]
    
    stats = {"CR": 0.0}
    result = engine.apply_set_bonus(stats, runes)
    assert result["CR"] == 12.0
    
    # Rage 4-set: CD +40
    runes = [
        Rune(rune_id=i, slot=i, set_id=10, main_stat_id=1, main_stat_value=100.0, subs=[], level=15, quality=6)
        for i in range(1, 5)
    ]
    stats = {"CD": 0.0}
    result = engine.apply_set_bonus(stats, runes)
    assert result["CD"] == 40.0

