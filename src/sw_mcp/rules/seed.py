"""Build and seed ruleset from sources"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .schema import (
    Ruleset, Metadata, Source, RuneRules, SetRules, SetBonus,
    GemGrindRules, GemGrindCap, SubstatsRules, SubstatsRange, ContentRules
)
from .loader import save_ruleset_to_db, load_ruleset_from_db
from ..db.repo import SwarfarmRepository
from ..db.models import SwarfarmRaw


def load_swarfarm_entities(repo: SwarfarmRepository) -> Dict[str, Any]:
    """
    Load base entities from SWARFARM DB
    
    Returns:
        Dictionary with entities by endpoint
    """
    entities = {}
    
    # Load monsters
    monsters_raw = repo.session.query(SwarfarmRaw).filter(
        SwarfarmRaw.endpoint == "monsters"
    ).all()
    entities["monsters"] = [json.loads(r.payload_json) for r in monsters_raw]
    
    # Load skills
    skills_raw = repo.session.query(SwarfarmRaw).filter(
        SwarfarmRaw.endpoint == "skills"
    ).all()
    entities["skills"] = [json.loads(r.payload_json) for r in skills_raw]
    
    # Load items
    items_raw = repo.session.query(SwarfarmRaw).filter(
        SwarfarmRaw.endpoint == "items"
    ).all()
    entities["items"] = [json.loads(r.payload_json) for r in items_raw]
    
    return entities


def load_overlay(overlay_path: str) -> Dict[str, Any]:
    """Load overlay file"""
    with open(overlay_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_ruleset_v1(
    overlay_path: Optional[str] = None,
    swarfarm_entities: Optional[Dict[str, Any]] = None
) -> Ruleset:
    """
    Build ruleset v1 from sources
    
    Args:
        overlay_path: Path to overlay JSON file
        swarfarm_entities: Pre-loaded SWARFARM entities (optional)
    
    Returns:
        Built Ruleset
    """
    # Load overlay if provided
    overlay = {}
    if overlay_path and Path(overlay_path).exists():
        overlay = load_overlay(overlay_path)
    
    # Default rune rules (from our discussions)
    rune_rules = RuneRules(
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
    )
    
    # Override with overlay if present
    if "rune_rules" in overlay:
        rune_rules = RuneRules(**overlay["rune_rules"])
    
    # Default set rules
    set_rules_dict = {
        1: SetBonus(set_id=1, set_name="Energy", bonus_2={"HP_PCT": 15.0}),
        2: SetBonus(set_id=2, set_name="Blade", bonus_2={"CR": 12.0}),
        3: SetBonus(set_id=3, set_name="Swift", bonus_2={"SPD_PCT": 25.0}),
        4: SetBonus(set_id=4, set_name="Violent", bonus_2={"VIOLENT": 22.0}),  # Special
        5: SetBonus(set_id=5, set_name="Focus", bonus_2={"ACC": 20.0}),
        6: SetBonus(set_id=6, set_name="Guard", bonus_2={"DEF_PCT": 15.0}),
        7: SetBonus(set_id=7, set_name="Endure", bonus_2={"RES": 20.0}),
        8: SetBonus(set_id=8, set_name="Fatal", bonus_4={"ATK_PCT": 35.0}),
        9: SetBonus(set_id=9, set_name="Despair", bonus_2={"DESPAIR": 25.0}),  # Special
        10: SetBonus(set_id=10, set_name="Rage", bonus_4={"CD": 40.0}),
        11: SetBonus(set_id=11, set_name="Will", bonus_2={"WILL": 1.0}),  # Special
        12: SetBonus(set_id=12, set_name="Nemesis", bonus_2={"NEMESIS": 4.0}),  # Special
        13: SetBonus(set_id=13, set_name="Shield", bonus_2={"SHIELD": 15.0}),  # Special
        14: SetBonus(set_id=14, set_name="Revenge", bonus_2={"REVENGE": 15.0}),  # Special
        15: SetBonus(set_id=15, set_name="Destroy", bonus_2={"DESTROY": 4.0}),  # Special
        16: SetBonus(set_id=16, set_name="Fight", bonus_2={"FIGHT": 8.0}),  # Special
        17: SetBonus(set_id=17, set_name="Determination", bonus_2={"DETERMINATION": 8.0}),  # Special
        18: SetBonus(set_id=18, set_name="Enhance", bonus_2={"ENHANCE": 8.0}),  # Special
        19: SetBonus(set_id=19, set_name="Accuracy", bonus_2={"ACC": 20.0}),
        20: SetBonus(set_id=20, set_name="Tolerance", bonus_2={"RES": 20.0}),
        25: SetBonus(set_id=25, set_name="Intangible", bonus_2={}),  # No bonus, can contribute to other sets
    }
    
    # Override with overlay if present
    if "set_rules" in overlay:
        for set_id_str, set_data in overlay["set_rules"].get("sets", {}).items():
            set_id = int(set_id_str)
            set_rules_dict[set_id] = SetBonus(**set_data)
    
    set_rules = SetRules(sets=set_rules_dict)
    
    # Default gem/grind rules
    gem_grind_rules = GemGrindRules(
        gem_allowed_stats=[1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],  # All stats except special
        grind_allowed_stats=[1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
        caps=[
            GemGrindCap(stat_id=1, stat_name="HP", normal_cap=1000, ancient_cap=1200),
            GemGrindCap(stat_id=2, stat_name="HP%", normal_cap=8.0, ancient_cap=10.0),
            GemGrindCap(stat_id=3, stat_name="ATK", normal_cap=100, ancient_cap=120),
            GemGrindCap(stat_id=4, stat_name="ATK%", normal_cap=8.0, ancient_cap=10.0),
            GemGrindCap(stat_id=5, stat_name="DEF", normal_cap=100, ancient_cap=120),
            GemGrindCap(stat_id=6, stat_name="DEF%", normal_cap=8.0, ancient_cap=10.0),
            GemGrindCap(stat_id=8, stat_name="SPD", normal_cap=4.0, ancient_cap=5.0),
            GemGrindCap(stat_id=9, stat_name="CR", normal_cap=4.0, ancient_cap=5.0),
            GemGrindCap(stat_id=10, stat_name="CD", normal_cap=4.0, ancient_cap=5.0),
            GemGrindCap(stat_id=11, stat_name="RES", normal_cap=4.0, ancient_cap=5.0),
            GemGrindCap(stat_id=12, stat_name="ACC", normal_cap=4.0, ancient_cap=5.0),
        ]
    )
    
    # Override with overlay if present
    if "gem_grind_rules" in overlay:
        gem_grind_rules = GemGrindRules(**overlay["gem_grind_rules"])
    
    # Default substats rules
    substats_rules = SubstatsRules(
        ranges=[
            SubstatsRange(stat_id=1, stat_name="HP", normal_min=160, normal_max=300, ancient_min=200, ancient_max=400),
            SubstatsRange(stat_id=2, stat_name="HP%", normal_min=4.0, normal_max=8.0, ancient_min=5.0, ancient_max=10.0),
            SubstatsRange(stat_id=3, stat_name="ATK", normal_min=10, normal_max=20, ancient_min=15, ancient_max=30),
            SubstatsRange(stat_id=4, stat_name="ATK%", normal_min=4.0, normal_max=8.0, ancient_min=5.0, ancient_max=10.0),
            SubstatsRange(stat_id=5, stat_name="DEF", normal_min=10, normal_max=20, ancient_min=15, ancient_max=30),
            SubstatsRange(stat_id=6, stat_name="DEF%", normal_min=4.0, normal_max=8.0, ancient_min=5.0, ancient_max=10.0),
            SubstatsRange(stat_id=8, stat_name="SPD", normal_min=4.0, normal_max=6.0, ancient_min=5.0, ancient_max=8.0),
            SubstatsRange(stat_id=9, stat_name="CR", normal_min=3.0, normal_max=6.0, ancient_min=4.0, ancient_max=8.0),
            SubstatsRange(stat_id=10, stat_name="CD", normal_min=3.0, normal_max=7.0, ancient_min=4.0, ancient_max=9.0),
            SubstatsRange(stat_id=11, stat_name="RES", normal_min=4.0, normal_max=8.0, ancient_min=5.0, ancient_max=10.0),
            SubstatsRange(stat_id=12, stat_name="ACC", normal_min=4.0, normal_max=8.0, ancient_min=5.0, ancient_max=10.0),
        ]
    )
    
    # Override with overlay if present
    if "substats_rules" in overlay:
        substats_rules = SubstatsRules(**overlay["substats_rules"])
    
    # Metadata
    sources = [
        Source(type="swarfarm", url="https://swarfarm.com/api/v2/"),
    ]
    if overlay_path:
        sources.append(Source(type="overlay", notes=overlay_path))
    
    metadata = Metadata(
        effective_date=overlay.get("metadata", {}).get("effective_date", "2024-01-01"),
        patch_version=overlay.get("metadata", {}).get("patch_version"),
        sources=sources,
        confidence=overlay.get("metadata", {}).get("confidence", "high"),
        notes=overlay.get("metadata", {}).get("notes")
    )
    
    # Build ruleset
    ruleset = Ruleset(
        version="v1.0.0",
        metadata=metadata,
        rune_rules=rune_rules,
        set_rules=set_rules,
        gem_grind_rules=gem_grind_rules,
        substats_rules=substats_rules,
        content_rules=ContentRules(),
    )
    
    return ruleset


def seed_ruleset(
    repo: SwarfarmRepository,
    version: str = "v1.0.0",
    overlay_path: Optional[str] = None
):
    """
    Seed ruleset to DB
    
    Args:
        repo: SwarfarmRepository instance
        version: Version tag
        overlay_path: Path to overlay JSON file
    """
    # Load SWARFARM entities
    swarfarm_entities = load_swarfarm_entities(repo)
    
    # Build ruleset
    ruleset = build_ruleset_v1(overlay_path=overlay_path, swarfarm_entities=swarfarm_entities)
    ruleset.version = version
    
    # Prepare sources JSON
    sources_json = {
        "swarfarm_entities": {
            "monsters": len(swarfarm_entities.get("monsters", [])),
            "skills": len(swarfarm_entities.get("skills", [])),
            "items": len(swarfarm_entities.get("items", [])),
        },
        "overlay_path": overlay_path,
    }
    
    # Save to DB
    save_ruleset_to_db(repo, ruleset, sources_json)
    
    # Set as current
    repo.set_current_ruleset(version)
    
    return ruleset


