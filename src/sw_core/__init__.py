"""SW Core - 서머너즈워 룬 최적화 엔진"""

__version__ = "1.0.0"

from .types import Rune, SubStat, BASE_CR, BASE_CD, MonsterBaseStats
from .swex_parser import parse_swex_json, load_swex_json
from .scoring import score_build, calculate_stats, get_objective_value, register_objective
from .optimizer import search_builds
from .rules import validate_rune, validate_build, filter_valid_runes
from .monster_registry import MonsterRegistry, get_registry, set_registry

__all__ = [
    "Rune",
    "SubStat",
    "BASE_CR",
    "BASE_CD",
    "MonsterBaseStats",
    "parse_swex_json",
    "load_swex_json",
    "score_build",
    "calculate_stats",
    "get_objective_value",
    "register_objective",
    "search_builds",
    "validate_rune",
    "validate_build",
    "filter_valid_runes",
    "MonsterRegistry",
    "get_registry",
    "set_registry",
]
