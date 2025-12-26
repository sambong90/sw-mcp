"""Pydantic models for ruleset schema"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SlotMainRule(BaseModel):
    """Slot main stat rules"""
    disallowed: List[int] = Field(default_factory=list, description="Disallowed main stat IDs")
    allowed: Optional[List[int]] = Field(None, description="Allowed main stat IDs (if specified, only these are allowed)")


class SlotSpecialRule(BaseModel):
    """Special rules for specific slots"""
    slot: int = Field(..., description="Slot number (1-6)")
    disallowed_main: List[int] = Field(default_factory=list, description="Disallowed main stat IDs")
    disallowed_sub: List[int] = Field(default_factory=list, description="Disallowed substat IDs")
    disallowed_prefix: List[int] = Field(default_factory=list, description="Disallowed prefix stat IDs")
    notes: Optional[str] = Field(None, description="Additional notes")


class RuneRules(BaseModel):
    """Rune legality rules"""
    slot_main_disallowed: Dict[int, List[int]] = Field(
        default_factory=dict,
        description="Slot -> list of disallowed main stat IDs"
    )
    slot_main_allowed: Optional[Dict[int, List[int]]] = Field(
        None,
        description="Slot -> list of allowed main stat IDs (if specified, only these are allowed)"
    )
    sub_disallowed: Dict[int, List[int]] = Field(
        default_factory=dict,
        description="Slot -> list of disallowed substat IDs"
    )
    sub_no_dup_main: bool = Field(True, description="Substats cannot duplicate main stat")
    slot_special_rules: List[SlotSpecialRule] = Field(
        default_factory=list,
        description="Special rules for specific slots"
    )


class SetBonus(BaseModel):
    """Set bonus definition"""
    set_id: int = Field(..., description="Set ID")
    set_name: str = Field(..., description="Set name")
    bonus_2: Optional[Dict[str, float]] = Field(None, description="2-set bonus: {stat_name: value}")
    bonus_4: Optional[Dict[str, float]] = Field(None, description="4-set bonus: {stat_name: value}")


class SetRules(BaseModel):
    """Set bonus rules"""
    sets: Dict[int, SetBonus] = Field(default_factory=dict, description="Set ID -> SetBonus")


class GemGrindCap(BaseModel):
    """Gem/Grind cap for a stat"""
    stat_id: int = Field(..., description="Stat ID")
    stat_name: str = Field(..., description="Stat name")
    normal_cap: Optional[float] = Field(None, description="Cap for normal runes")
    ancient_cap: Optional[float] = Field(None, description="Cap for ancient runes")


class GemGrindRules(BaseModel):
    """Gem and grind rules"""
    gem_allowed_stats: List[int] = Field(default_factory=list, description="Stat IDs that can be gemmed")
    grind_allowed_stats: List[int] = Field(default_factory=list, description="Stat IDs that can be grinded")
    caps: List[GemGrindCap] = Field(default_factory=list, description="Caps by stat and rune class")


class SubstatsRange(BaseModel):
    """Substat range definition"""
    stat_id: int = Field(..., description="Stat ID")
    stat_name: str = Field(..., description="Stat name")
    normal_min: Optional[float] = Field(None, description="Minimum for normal runes")
    normal_max: Optional[float] = Field(None, description="Maximum for normal runes")
    ancient_min: Optional[float] = Field(None, description="Minimum for ancient runes")
    ancient_max: Optional[float] = Field(None, description="Maximum for ancient runes")


class SubstatsRules(BaseModel):
    """Substat range rules"""
    ranges: List[SubstatsRange] = Field(default_factory=list, description="Substat ranges by stat and rune class")


class ContentRestriction(BaseModel):
    """Content-specific restriction"""
    content_id: Optional[str] = Field(None, description="Content ID")
    content_name: str = Field(..., description="Content name")
    restrictions: Dict[str, Any] = Field(default_factory=dict, description="Restriction rules (structure TBD)")


class ContentRules(BaseModel):
    """Content rules"""
    contents: List[ContentRestriction] = Field(default_factory=list, description="Content restrictions")


class Source(BaseModel):
    """Source of rule data"""
    url: Optional[str] = Field(None, description="Source URL")
    type: str = Field(..., description="Source type (swarfarm, overlay, manual, etc.)")
    notes: Optional[str] = Field(None, description="Additional notes")


class Metadata(BaseModel):
    """Ruleset metadata"""
    effective_date: str = Field(..., description="Date when ruleset becomes effective (YYYY-MM-DD)")
    patch_version: Optional[str] = Field(None, description="Game patch version")
    sources: List[Source] = Field(default_factory=list, description="Sources of rule data")
    confidence: Optional[str] = Field(None, description="Confidence level (high/medium/low)")
    notes: Optional[str] = Field(None, description="Additional notes")


class Ruleset(BaseModel):
    """Complete ruleset"""
    version: str = Field(..., description="Ruleset version tag")
    metadata: Metadata = Field(..., description="Metadata")
    rune_rules: RuneRules = Field(..., description="Rune legality rules")
    set_rules: SetRules = Field(..., description="Set bonus rules")
    gem_grind_rules: GemGrindRules = Field(..., description="Gem and grind rules")
    substats_rules: SubstatsRules = Field(..., description="Substat range rules")
    content_rules: ContentRules = Field(default_factory=ContentRules, description="Content rules")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "v1.0.0",
                "metadata": {
                    "effective_date": "2024-01-01",
                    "patch_version": "7.0.0",
                    "sources": [
                        {"type": "swarfarm", "url": "https://swarfarm.com/api/v2/"},
                        {"type": "overlay", "notes": "rune_numeric_rules_v1.json"}
                    ],
                    "confidence": "high"
                },
                "rune_rules": {
                    "slot_main_disallowed": {
                        "2": [10, 9, 11, 12],  # CD, CR, RES, ACC
                        "4": [8, 11, 12],  # SPD, RES, ACC
                        "6": [8, 10, 9]  # SPD, CD, CR
                    },
                    "sub_no_dup_main": True,
                    "slot_special_rules": [
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
                },
                "set_rules": {
                    "sets": {
                        "1": {
                            "set_id": 1,
                            "set_name": "Energy",
                            "bonus_2": {"HP_PCT": 15.0}
                        },
                        "10": {
                            "set_id": 10,
                            "set_name": "Rage",
                            "bonus_4": {"CD": 40.0}
                        }
                    }
                }
            }
        }

