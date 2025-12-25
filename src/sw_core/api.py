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
    base_atk: int = 900,
    base_spd: int = 104,
    require_sets: bool = True,
    max_candidates_per_slot: int = 300,
    max_results: int = 2000
) -> Dict[str, Any]:
    """
    Stable API for running rune optimization searches.
    
    This function provides a unified interface for both simple optimization
    and constraint-based searches.
    
    Args:
        runes: List of Rune objects to search
        target: "A" (Rage+Blade) or "B" (Fatal+Blade)
        mode: "exhaustive" (guaranteed complete) or "fast" (heuristic pruning)
        constraints: Optional dict of minimum constraints (e.g., {"CR": 100, "SPD": 100})
        objective: Sort objective ("SCORE", "ATK_TOTAL", "ATK_BONUS", "CD", "SPD")
        top_n: Number of top results to return
        return_policy: "top_n" or "all_at_best"
        base_atk: Base attack stat
        base_spd: Base speed stat
        require_sets: If True, enforce target set requirements; if False, allow any sets
        max_candidates_per_slot: For fast mode, max candidates per slot
        max_results: For fast mode, max results limit
    
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
        ...     constraints={"CR": 100, "SPD": 100},
        ...     objective="SCORE",
        ...     top_n=10
        ... )
        >>> print(f"Found {result['total_found']} builds")
        >>> for build in result['results']:
        ...     print(f"Score: {build['score']}")
    """
    if constraints is None:
        constraints = {}
    
    # Use search_builds for constraint-based searches, optimize_lushen for simple top-N
    if constraints or objective != "SCORE" or return_policy != "top_n" or not require_sets:
        # Use search_builds for advanced features
        results = search_builds(
            runes=runes,
            target=target,
            base_atk=base_atk,
            base_spd=base_spd,
            constraints=constraints,
            objective=objective,
            top_n=top_n,
            return_policy=return_policy,
            max_results=max_results,
            max_candidates_per_slot=max_candidates_per_slot,
            mode=mode,
            require_sets=require_sets
        )
    else:
        # Use optimize_lushen for simple top-N searches
        results = optimize_lushen(
            runes=runes,
            target=target,
            base_atk=base_atk,
            top_n=top_n,
            max_candidates_per_slot=max_candidates_per_slot,
            mode=mode
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
            "base_atk": base_atk,
            "base_spd": base_spd,
            "require_sets": require_sets,
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

