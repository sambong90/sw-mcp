"""Stable Python API for rune optimization"""

from typing import List, Dict, Optional, Any
from .types import Rune
from .swex_parser import parse_swex_json, load_swex_json
from .optimizer import optimize_lushen, search_builds


def run_search(
    runes: List[Rune],
    target: str = "B",
    mode: str = "exhaustive",
    constraints: Optional[Dict[str, float]] = None,
    objective: str = "SCORE",
    top_n: int = 20,
    return_policy: str = "top_n",
    return_all: bool = False,
    base_atk: int = 900,
    base_spd: int = 104,
    require_sets: bool = True,
    allow_any_main: bool = False,
    max_candidates_per_slot: int = 300,
    max_results: int = 2000
) -> Dict[str, Any]:
    """
    Stable API for running rune optimization searches (SWOP 스타일).
    
    ⚠️ 중요: exhaustive 모드에서는 정확도 100% 보장
    - exhaustive: feasibility pruning과 upper-bound pruning만 사용 (누락 없음)
    - fast: 정확도 보장 없음 (heuristic pruning 사용)
    
    Args:
        runes: List of Rune objects to search
        target: "A" (Rage+Blade) or "B" (Fatal+Blade)
        mode: "exhaustive" (정확도 100% 보장) or "fast" (정확도 보장 없음)
        constraints: Optional dict of minimum constraints (e.g., {"CR": 100, "SPD": 100, "ATK_TOTAL": 2000, "MIN_SCORE": 4800})
        objective: Sort objective ("SCORE", "ATK_TOTAL", "ATK_BONUS", "CD", "SPD")
        top_n: Number of top results to return (return_all=False일 때만 적용)
        return_policy: "top_n" or "all_at_best"
        return_all: If True, return all matching builds (메모리 주의)
        base_atk: Base attack stat
        base_spd: Base speed stat
        require_sets: If True, enforce target set requirements; if False, allow any sets
        allow_any_main: If True, allow any main stat for slot 2/4/6 (preset 해제)
        max_candidates_per_slot: For fast mode only, max candidates per slot
        max_results: For fast mode only, max results limit
    
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
        >>> result = run_search(
        ...     runes=runes,
        ...     target="B",
        ...     mode="exhaustive",
        ...     constraints={"CR": 100, "SPD": 100, "MIN_SCORE": 4800},
        ...     objective="SCORE",
        ...     top_n=10
        ... )
        >>> print(f"Found {result['total_found']} builds")
    """
    if constraints is None:
        constraints = {}
    
    # Always use search_builds for unified API
    results = search_builds(
        runes=runes,
        target=target,
        base_atk=base_atk,
        base_spd=base_spd,
        constraints=constraints,
        objective=objective,
        top_n=top_n,
        return_policy=return_policy,
        return_all=return_all,
        max_results=max_results,
        max_candidates_per_slot=max_candidates_per_slot,
        mode=mode,
        require_sets=require_sets,
        allow_any_main=allow_any_main
    )
    
    return {
        "results": results,
        "total_found": len(results),
        "search_params": {
            "target": target,
            "mode": mode,
            "constraints": constraints,
            "objective": objective,
            "top_n": top_n,
            "return_policy": return_policy,
            "return_all": return_all,
            "base_atk": base_atk,
            "base_spd": base_spd,
            "require_sets": require_sets,
            "allow_any_main": allow_any_main,
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

