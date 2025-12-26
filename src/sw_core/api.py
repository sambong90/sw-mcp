"""Stable Python API for rune optimization"""

from typing import List, Dict, Optional, Any
from .types import Rune
from .swex_parser import parse_swex_json, load_swex_json
from .optimizer import search_builds
from .monster_registry import get_registry, MonsterRegistry


def run_search(
    runes: List[Rune],
    base_atk: int = None,
    base_spd: int = None,
    base_hp: int = None,
    base_def: int = None,
    monster: Optional[Dict[str, Any]] = None,
    constraints: Optional[Dict[str, float]] = None,
    set_constraints: Optional[Dict[str, int]] = None,
    objective: str = "SCORE",
    top_n: int = 20,
    return_policy: str = "top_n",
    return_all: bool = False,
    max_candidates_per_slot: int = 300,
    max_results: int = 2000,
    mode: str = "exhaustive",
    registry: Optional[MonsterRegistry] = None
) -> Dict[str, Any]:
    """
    범용 룬 빌드 탐색 API (SWOP 스타일)
    
    ⚠️ 중요: exhaustive 모드에서는 정확도 100% 보장
    - exhaustive: feasibility pruning과 upper-bound pruning만 사용 (누락 없음)
    - fast: 정확도 보장 없음 (heuristic pruning 사용)
    
    Args:
        runes: List of Rune objects to search (모든 세트 포함)
        base_atk: Base attack stat (monster 지정 시 자동 조회)
        base_spd: Base speed stat (monster 지정 시 자동 조회)
        base_hp: Base HP stat (monster 지정 시 자동 조회)
        base_def: Base defense stat (monster 지정 시 자동 조회)
        monster: 몬스터 정보 {"master_id": 14105} 또는 {"name": "Lushen"} (레지스트리에서 자동 조회)
        constraints: Optional dict of minimum constraints (e.g., {"CR": 100, "SPD": 100, "ATK_TOTAL": 2000, "MIN_SCORE": 4800})
        set_constraints: Optional dict of set requirements (e.g., {"Rage": 4, "Blade": 2}). None이면 모든 세트 허용
        objective: Objective function ("SCORE", "ATK_TOTAL", "EHP", "SPD", "DAMAGE_PROXY" 등)
        top_n: Number of top results to return (return_all=False일 때만 적용)
        return_policy: "top_n" or "all_at_best"
        return_all: If True, return all matching builds (메모리 주의)
        max_candidates_per_slot: For fast mode only, max candidates per slot
        max_results: For fast mode only, max results limit
        mode: "exhaustive" (정확도 100% 보장) or "fast" (정확도 보장 없음)
        registry: MonsterRegistry 인스턴스 (기본: 전역 레지스트리)
    
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
        >>> # 몬스터 레지스트리 사용 (자동 조회)
        >>> result = run_search(
        ...     runes=runes,
        ...     monster={"master_id": 14105},  # 루쉔
        ...     constraints={"CR": 100, "SPD": 100},
        ...     objective="SCORE"
        ... )
        >>> 
        >>> # 이름으로 조회
        >>> result = run_search(
        ...     runes=runes,
        ...     monster={"name": "Lushen"},
        ...     constraints={"CR": 100}
        ... )
        >>> 
        >>> # 수동으로 base stats 지정 (레거시 호환)
        >>> result = run_search(
        ...     runes=runes,
        ...     base_atk=900,
        ...     base_spd=104,
        ...     constraints={"CR": 100}
        ... )
    """
    # 레지스트리에서 base stats 조회
    if monster:
        if registry is None:
            registry = get_registry()
        
        monster_stats = registry.get(
            master_id=monster.get("master_id"),
            name=monster.get("name")
        )
        
        if monster_stats:
            # 레지스트리에서 조회된 값 사용
            base_atk = base_atk if base_atk is not None else monster_stats.base_atk
            base_spd = base_spd if base_spd is not None else monster_stats.base_spd
            base_hp = base_hp if base_hp is not None else monster_stats.base_hp
            base_def = base_def if base_def is not None else monster_stats.base_def
        else:
            # 조회 실패 시 기본값 사용
            registry_default = registry.get_default()
            base_atk = base_atk if base_atk is not None else registry_default.base_atk
            base_spd = base_spd if base_spd is not None else registry_default.base_spd
            base_hp = base_hp if base_hp is not None else registry_default.base_hp
            base_def = base_def if base_def is not None else registry_default.base_def
    else:
        # 레거시 호환: base_* 인자가 없으면 기본값 사용
        registry_default = get_registry().get_default()
        base_atk = base_atk if base_atk is not None else registry_default.base_atk
        base_spd = base_spd if base_spd is not None else registry_default.base_spd
        base_hp = base_hp if base_hp is not None else registry_default.base_hp
        base_def = base_def if base_def is not None else registry_default.base_def
    
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
