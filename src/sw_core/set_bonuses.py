"""Data-driven set bonus system for ALL rune sets"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SetBonusDefinition:
    """Set bonus definition"""
    set_id: int
    set_name: str
    bonus_2: Optional[Dict[str, float]] = None  # {stat_name: value} for 2-set
    bonus_4: Optional[Dict[str, float]] = None  # {stat_name: value} for 4-set
    is_proc_set: bool = False  # True for Violent/Will/Despair/etc (non-stat affecting)


# Canonical set bonus definitions for ALL sets
# Stat-affecting sets: apply bonuses to computed stats
# Proc sets: store metadata but don't alter stats
SET_BONUS_DEFINITIONS: Dict[int, SetBonusDefinition] = {
    # Stat-affecting sets
    1: SetBonusDefinition(set_id=1, set_name="Energy", bonus_2={"HP_PCT": 15.0}),
    2: SetBonusDefinition(set_id=2, set_name="Guard", bonus_2={"DEF_PCT": 15.0}),
    3: SetBonusDefinition(set_id=3, set_name="Swift", bonus_2={"SPD_PCT": 25.0}),  # Special: applies to base SPD
    4: SetBonusDefinition(set_id=4, set_name="Blade", bonus_2={"CR": 12.0}),
    5: SetBonusDefinition(set_id=5, set_name="Rage", bonus_4={"CD": 40.0}),
    6: SetBonusDefinition(set_id=6, set_name="Focus", bonus_2={"ACC": 20.0}),
    7: SetBonusDefinition(set_id=7, set_name="Endure", bonus_2={"RES": 20.0}),
    8: SetBonusDefinition(set_id=8, set_name="Fatal", bonus_4={"ATK_PCT": 35.0}),
    9: SetBonusDefinition(set_id=9, set_name="Despair", is_proc_set=True),  # Proc set
    10: SetBonusDefinition(set_id=10, set_name="Vampire", is_proc_set=True),  # Proc set
    11: SetBonusDefinition(set_id=11, set_name="Violent", is_proc_set=True),  # Proc set
    12: SetBonusDefinition(set_id=12, set_name="Nemesis", is_proc_set=True),  # Proc set
    13: SetBonusDefinition(set_id=13, set_name="Will", is_proc_set=True),  # Proc set
    14: SetBonusDefinition(set_id=14, set_name="Shield", is_proc_set=True),  # Proc set
    15: SetBonusDefinition(set_id=15, set_name="Revenge", is_proc_set=True),  # Proc set
    16: SetBonusDefinition(set_id=16, set_name="Destroy", is_proc_set=True),  # Proc set
    17: SetBonusDefinition(set_id=17, set_name="Fight", bonus_2={"ATK_PCT": 8.0}),  # Guild set
    18: SetBonusDefinition(set_id=18, set_name="Determination", bonus_2={"DEF_PCT": 8.0}),  # Guild set
    19: SetBonusDefinition(set_id=19, set_name="Enhance", bonus_2={"HP_PCT": 8.0}),  # Guild set
    20: SetBonusDefinition(set_id=20, set_name="Accuracy", bonus_2={"ACC": 20.0}),
    21: SetBonusDefinition(set_id=21, set_name="Tolerance", bonus_2={"RES": 20.0}),
    25: SetBonusDefinition(set_id=25, set_name="Intangible", is_proc_set=True),  # Wildcard set
}


def get_set_bonus_definition(set_id: int) -> Optional[SetBonusDefinition]:
    """Get set bonus definition by set_id"""
    return SET_BONUS_DEFINITIONS.get(set_id)


def load_set_bonuses_from_ruleset(ruleset) -> Dict[int, SetBonusDefinition]:
    """
    Load set bonuses from ruleset (if available)
    
    Args:
        ruleset: Ruleset object from rules module
    
    Returns:
        Dict of set_id -> SetBonusDefinition
    """
    if ruleset is None:
        return SET_BONUS_DEFINITIONS.copy()
    
    # Merge ruleset set_rules with defaults
    result = SET_BONUS_DEFINITIONS.copy()
    
    if hasattr(ruleset, 'set_rules') and hasattr(ruleset.set_rules, 'sets'):
        for set_id, set_bonus in ruleset.set_rules.sets.items():
            bonus_2 = set_bonus.bonus_2 if hasattr(set_bonus, 'bonus_2') else None
            bonus_4 = set_bonus.bonus_4 if hasattr(set_bonus, 'bonus_4') else None
            is_proc = not (bonus_2 or bonus_4)
            
            result[set_id] = SetBonusDefinition(
                set_id=set_id,
                set_name=set_bonus.set_name if hasattr(set_bonus, 'set_name') else f"Set_{set_id}",
                bonus_2=bonus_2,
                bonus_4=bonus_4,
                is_proc_set=is_proc
            )
    
    return result


