"""Stable Python API for rune optimization"""

from typing import List, Dict, Optional, Any
from .types import Rune
from .swex_parser import parse_swex_json, load_swex_json
from .optimizer import search_builds


def run_search(
    runes: List[Rune],
    base_atk: int = 900,
    base_spd: int = 104,
    base_hp: int = 10000,
    base_def: int = 500,
    constraints: Optional[Dict[str, float]] = None,
    set_constraints: Optional[Dict[str, int]] = None,
    objective: str = "SCORE",
    top_n: int = 20,
    return_policy: str = "top_n",
    return_all: bool = False,
    max_candidates_per_slot: int = 300,
    max_results: int = 2000,
    mode: str = "exhaustive"
) -> Dict[str, Any]:
    """
    범용 룬 빌드 탐색 API (SWOP 스타일)
    
    ⚠️ 중요: exhaustive 모드에서는 정확도 100% 보장
    - exhaustive: feasibility pruning과 upper-bound pruning만 사용 (누락 없음)
    - fast: 정확도 보장 없음 (heuristic pruning 사용)
    
    Args:
        runes: List of Rune objects to search (모든 세트 포함)
        base_atk: Base attack stat
        base_spd: Base speed stat
        base_hp: Base HP stat
        base_def: Base defense stat
        constraints: Optional dict of minimum constraints (e.g., {"CR": 100, "SPD": 100, "ATK_TOTAL": 2000, "MIN_SCORE": 4800})
        set_constraints: Optional dict of set requirements (e.g., {"Rage": 4, "Blade": 2}). None이면 모든 세트 허용
        objective: Objective function ("SCORE", "ATK_TOTAL", "EHP", "SPD", "DAMAGE_PROXY" 등)
        top_n: Number of top results to return (return_all=False일 때만 적용)
        return_policy: "top_n" or "all_at_best"
        return_all: If True, return all matching builds (메모리 주의)
        max_candidates_per_slot: For fast mode only, max candidates per slot
        max_results: For fast mode only, max results limit
        mode: "exhaustive" (정확도 100% 보장) or "fast" (정확도 보장 없음)
    
    Returns:
        Dict with:
            - results: List of build results
            - total_found: Total number of valid builds found
            - search_params: Parameters used for search
            - mode: Search mode used
    
    Examples:
        >>> from src.sw_core.api import run_search
        >>> from src.sw_core.swex_parser import load_swex_json
        >>> 
        >>> runes = load_swex_json("swex_export.json")
        >>> 
        >>> # 범용 탐색 (모든 세트 허용)
        >>> result = run_search(
        ...     runes=runes,
        ...     base_atk=900,
        ...     base_spd=104,
        ...     constraints={"CR": 100, "SPD": 100},
        ...     objective="SCORE",
        ...     top_n=10
        ... )
        >>> 
        >>> # 특정 세트 조건 (Rage 4 + Blade 2)
        >>> result = run_search(
        ...     runes=runes,
        ...     set_constraints={"Rage": 4, "Blade": 2},
        ...     constraints={"CR": 100},
        ...     objective="SCORE"
        ... )
        >>> 
        >>> # 다른 몬스터 (예: 탱커)
        >>> result = run_search(
        ...     runes=runes,
        ...     base_hp=15000,
        ...     base_def=800,
        ...     constraints={"HP_TOTAL": 30000, "DEF_TOTAL": 1500},
        ...     objective="EHP"
        ... )
    """
    results = search_builds(
        runes=runes,
        base_atk=base_atk,
        base_spd=base_spd,
        base_hp=base_hp,
        base_def=base_def,
        constraints=constraints,
        set_constraints=set_constraints,
        objective=objective,
        top_n=top_n,
        return_policy=return_policy,
        return_all=return_all,
        max_results=max_results,
        max_candidates_per_slot=max_candidates_per_slot,
        mode=mode
    )
    
    return {
        "results": results,
        "total_found": len(results),
        "search_params": {
            "base_atk": base_atk,
            "base_spd": base_spd,
            "base_hp": base_hp,
            "base_def": base_def,
            "constraints": constraints,
            "set_constraints": set_constraints,
            "objective": objective,
            "top_n": top_n,
            "return_policy": return_policy,
            "return_all": return_all,
        },
        "mode": mode,
    }


def run_search_from_json(
    json_data: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """
    Run search from SWEX JSON data.
    
    Args:
        json_data: SWEX JSON dictionary
        **kwargs: Same as run_search() parameters
    
    Returns:
        Same as run_search()
    """
    runes = parse_swex_json(json_data)
    return run_search(runes=runes, **kwargs)


def run_search_from_file(
    file_path: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Run search from SWEX JSON file.
    
    Args:
        file_path: Path to SWEX JSON file
        **kwargs: Same as run_search() parameters
    
    Returns:
        Same as run_search()
    """
    runes = load_swex_json(file_path)
    return run_search(runes=runes, **kwargs)
