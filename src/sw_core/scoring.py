"""Generic stat calculation for ALL rune sets"""

from typing import List, Tuple, Dict, Callable, Optional
from .types import Rune, BASE_CR, BASE_CD, STAT_ID_NAME, SET_ID_NAME
from .set_bonuses import SET_BONUS_DEFINITIONS, get_set_bonus_definition, load_set_bonuses_from_ruleset, SetBonusDefinition


def count_sets(runes: List[Rune], intangible_assignment: Dict[int, int] = None) -> Dict[int, int]:
    """
    Count sets (supports multiple intangible runes)
    
    Args:
        runes: List of runes
        intangible_assignment: {rune_id: target_set_id} for intangible runes
    
    Returns:
        {set_id: count} dictionary
    """
    if intangible_assignment is None:
        intangible_assignment = {}
    
    set_counts = {}
    
    for rune in runes:
        if rune.intangible:
            # Intangible rune: assign to target set if specified
            target_set_id = intangible_assignment.get(rune.rune_id)
            if target_set_id is not None:
                set_counts[target_set_id] = set_counts.get(target_set_id, 0) + 1
            # If not assigned, it doesn't contribute to any set
        else:
            set_counts[rune.set_id] = set_counts.get(rune.set_id, 0) + 1
    
    return set_counts


def apply_set_bonuses(
    base_stats: Dict[str, float],
    rune_stats: Dict[str, float],
    set_counts: Dict[int, int],
    set_bonus_defs: Optional[Dict[int, SetBonusDefinition]] = None
) -> Dict[str, float]:
    """
    Apply set bonuses to stats (data-driven, supports ALL sets)
    
    Args:
        base_stats: Base stats {base_atk, base_spd, base_hp, base_def}
        rune_stats: Stats from runes {atk_pct_total, atk_flat_total, spd_total, ...}
        set_counts: {set_id: count} from count_sets()
        set_bonus_defs: Optional set bonus definitions (defaults to SET_BONUS_DEFINITIONS)
    
    Returns:
        Final derived stats
    """
    if set_bonus_defs is None:
        set_bonus_defs = SET_BONUS_DEFINITIONS
    
    # Start with rune stats
    final_stats = rune_stats.copy()
    
    # Apply stat-affecting set bonuses
    for set_id, count in set_counts.items():
        bonus_def = set_bonus_defs.get(set_id)
        if bonus_def is None or bonus_def.is_proc_set:
            continue  # Skip proc sets and unknown sets
        
        # Apply 2-set bonus
        if count >= 2 and bonus_def.bonus_2:
            for stat_name, value in bonus_def.bonus_2.items():
                if stat_name == "HP_PCT":
                    final_stats["hp_pct_total"] = final_stats.get("hp_pct_total", 0.0) + value
                elif stat_name == "ATK_PCT":
                    final_stats["atk_pct_total"] = final_stats.get("atk_pct_total", 0.0) + value
                elif stat_name == "DEF_PCT":
                    final_stats["def_pct_total"] = final_stats.get("def_pct_total", 0.0) + value
                elif stat_name == "SPD_PCT":
                    # Swift: applies to base SPD only
                    final_stats["spd_pct_from_swift"] = value
                elif stat_name == "CR":
                    final_stats["cr_total"] = final_stats.get("cr_total", 0.0) + value
                elif stat_name == "CD":
                    final_stats["cd_total"] = final_stats.get("cd_total", 0.0) + value
                elif stat_name == "ACC":
                    final_stats["acc_total"] = final_stats.get("acc_total", 0.0) + value
                elif stat_name == "RES":
                    final_stats["res_total"] = final_stats.get("res_total", 0.0) + value
        
        # Apply 4-set bonus
        if count >= 4 and bonus_def.bonus_4:
            for stat_name, value in bonus_def.bonus_4.items():
                if stat_name == "HP_PCT":
                    final_stats["hp_pct_total"] = final_stats.get("hp_pct_total", 0.0) + value
                elif stat_name == "ATK_PCT":
                    final_stats["atk_pct_total"] = final_stats.get("atk_pct_total", 0.0) + value
                elif stat_name == "DEF_PCT":
                    final_stats["def_pct_total"] = final_stats.get("def_pct_total", 0.0) + value
                elif stat_name == "CD":
                    final_stats["cd_total"] = final_stats.get("cd_total", 0.0) + value
    
    # Calculate final totals with rounding (deterministic integer math)
    base_atk = base_stats.get("base_atk", 900)
    base_spd = base_stats.get("base_spd", 104)
    base_hp = base_stats.get("base_hp", 10000)
    base_def = base_stats.get("base_def", 500)
    
    # HP: base * (1 + pct_total/100) + flat_total (round down)
    hp_pct = final_stats.get("hp_pct_total", 0.0)
    hp_flat = final_stats.get("hp_flat_total", 0.0)
    hp_bonus = int(base_hp * (hp_pct / 100.0)) + int(hp_flat)
    final_stats["hp_total"] = base_hp + hp_bonus
    final_stats["hp_bonus"] = hp_bonus
    
    # ATK: base * (1 + pct_total/100) + flat_total (round down)
    atk_pct = final_stats.get("atk_pct_total", 0.0)
    atk_flat = final_stats.get("atk_flat_total", 0.0)
    atk_bonus = int(base_atk * (atk_pct / 100.0)) + int(atk_flat)
    final_stats["atk_total"] = base_atk + atk_bonus
    final_stats["atk_bonus"] = atk_bonus
    
    # DEF: base * (1 + pct_total/100) + flat_total (round down)
    def_pct = final_stats.get("def_pct_total", 0.0)
    def_flat = final_stats.get("def_flat_total", 0.0)
    def_bonus = int(base_def * (def_pct / 100.0)) + int(def_flat)
    final_stats["def_total"] = base_def + def_bonus
    final_stats["def_bonus"] = def_bonus
    
    # SPD: base_spd * (1 + swift_pct_if_any/100) + flat_spd (round down)
    spd_flat = final_stats.get("spd_total", 0.0)
    swift_pct = final_stats.get("spd_pct_from_swift", 0.0)
    spd_bonus = int(base_spd * (swift_pct / 100.0)) + int(spd_flat)
    final_stats["spd_total"] = base_spd + spd_bonus
    
    # CR/CD/ACC/RES are additive (already in final_stats)
    
    return final_stats


def calculate_stats(
    runes: List[Rune],
    base_atk: int = 900,
    base_spd: int = 104,
    base_hp: int = 10000,
    base_def: int = 500,
    base_cr: int = BASE_CR,
    base_cd: int = BASE_CD,
    intangible_assignment: Dict[int, int] = None,
    set_bonus_defs: Optional[Dict[int, SetBonusDefinition]] = None
) -> Dict[str, float]:
    """
    Calculate stats from runes (generic for ALL sets)
    
    Args:
        runes: List of 6 runes
        base_atk: Base attack
        base_spd: Base speed
        base_hp: Base HP
        base_def: Base defense
        base_cr: Base crit rate
        base_cd: Base crit damage
        intangible_assignment: {rune_id: target_set_id} for intangible runes
        set_bonus_defs: Optional set bonus definitions
    
    Returns:
        Complete stats dictionary
    """
    if intangible_assignment is None:
        intangible_assignment = {}
    
    # Initialize stats from base values
    rune_stats = {
        "cr_total": float(base_cr),
        "cd_total": float(base_cd),
        "atk_pct_total": 0.0,
        "atk_flat_total": 0.0,
        "hp_pct_total": 0.0,
        "hp_flat_total": 0.0,
        "def_pct_total": 0.0,
        "def_flat_total": 0.0,
        "spd_total": 0.0,
        "res_total": 0.0,
        "acc_total": 0.0,
    }
    
    # Sum stats from runes
    for rune in runes:
        # Main stat
        if rune.main_stat_id == 1:  # HP
            rune_stats["hp_flat_total"] += rune.main_stat_value
        elif rune.main_stat_id == 2:  # HP%
            rune_stats["hp_pct_total"] += rune.main_stat_value
        elif rune.main_stat_id == 3:  # ATK
            rune_stats["atk_flat_total"] += rune.main_stat_value
        elif rune.main_stat_id == 4:  # ATK%
            rune_stats["atk_pct_total"] += rune.main_stat_value
        elif rune.main_stat_id == 5:  # DEF
            rune_stats["def_flat_total"] += rune.main_stat_value
        elif rune.main_stat_id == 6:  # DEF%
            rune_stats["def_pct_total"] += rune.main_stat_value
        elif rune.main_stat_id == 8:  # SPD
            rune_stats["spd_total"] += rune.main_stat_value
        elif rune.main_stat_id == 9:  # CR
            rune_stats["cr_total"] += rune.main_stat_value
        elif rune.main_stat_id == 10:  # CD
            rune_stats["cd_total"] += rune.main_stat_value
        elif rune.main_stat_id == 11:  # RES
            rune_stats["res_total"] += rune.main_stat_value
        elif rune.main_stat_id == 12:  # ACC
            rune_stats["acc_total"] += rune.main_stat_value
        
        # Prefix
        if rune.has_prefix:
            if rune.prefix_stat_id == 1:
                rune_stats["hp_flat_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 2:
                rune_stats["hp_pct_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 3:
                rune_stats["atk_flat_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 4:
                rune_stats["atk_pct_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 5:
                rune_stats["def_flat_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 6:
                rune_stats["def_pct_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 8:
                rune_stats["spd_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 9:
                rune_stats["cr_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 10:
                rune_stats["cd_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 11:
                rune_stats["res_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 12:
                rune_stats["acc_total"] += rune.prefix_stat_value
        
        # Substats
        for sub in rune.subs:
            if sub.stat_id == 1:
                rune_stats["hp_flat_total"] += sub.value
            elif sub.stat_id == 2:
                rune_stats["hp_pct_total"] += sub.value
            elif sub.stat_id == 3:
                rune_stats["atk_flat_total"] += sub.value
            elif sub.stat_id == 4:
                rune_stats["atk_pct_total"] += sub.value
            elif sub.stat_id == 5:
                rune_stats["def_flat_total"] += sub.value
            elif sub.stat_id == 6:
                rune_stats["def_pct_total"] += sub.value
            elif sub.stat_id == 8:
                rune_stats["spd_total"] += sub.value
            elif sub.stat_id == 9:
                rune_stats["cr_total"] += sub.value
            elif sub.stat_id == 10:
                rune_stats["cd_total"] += sub.value
            elif sub.stat_id == 11:
                rune_stats["res_total"] += sub.value
            elif sub.stat_id == 12:
                rune_stats["acc_total"] += sub.value
    
    # Count sets
    set_counts = count_sets(runes, intangible_assignment)
    
    # Apply set bonuses
    base_stats = {
        "base_atk": base_atk,
        "base_spd": base_spd,
        "base_hp": base_hp,
        "base_def": base_def,
    }
    
    final_stats = apply_set_bonuses(base_stats, rune_stats, set_counts, set_bonus_defs)
    
    return final_stats


# Objective functions (pluggable)
OBJECTIVE_FUNCTIONS: Dict[str, Callable[[Dict[str, float]], float]] = {}


def register_objective(name: str, func: Callable[[Dict[str, float]], float]):
    """Register objective function"""
    OBJECTIVE_FUNCTIONS[name] = func


def get_objective_value(objective: str, stats: Dict[str, float]) -> float:
    """Get objective value"""
    if objective in OBJECTIVE_FUNCTIONS:
        return OBJECTIVE_FUNCTIONS[objective](stats)
    
    # Default objectives
    if objective == "SCORE":
        # Generic score: (cd_total * 10) + atk_bonus + 200
        return (stats.get("cd_total", 0) * 10) + stats.get("atk_bonus", 0) + 200
    elif objective == "ATK_TOTAL":
        return stats.get("atk_total", 0)
    elif objective == "ATK_BONUS":
        return stats.get("atk_bonus", 0)
    elif objective == "HP_TOTAL":
        return stats.get("hp_total", 0)
    elif objective == "DEF_TOTAL":
        return stats.get("def_total", 0)
    elif objective == "CD":
        return stats.get("cd_total", 0)
    elif objective == "CR":
        return stats.get("cr_total", 0)
    elif objective == "SPD":
        return stats.get("spd_total", 0)
    elif objective == "EHP":
        # Effective HP: HP * (1 + DEF/1000)
        hp = stats.get("hp_total", 0)
        def_val = stats.get("def_total", 0)
        return hp * (1 + def_val / 1000.0)
    elif objective == "DAMAGE_PROXY":
        # Damage proxy: ATK * (1 + CD/100) * (1 + CR/100)
        atk = stats.get("atk_total", 0)
        cd = stats.get("cd_total", 0)
        cr = min(stats.get("cr_total", 0), 100.0)
        return atk * (1 + cd / 100.0) * (1 + cr / 100.0)
    else:
        # Default: SCORE
        return (stats.get("cd_total", 0) * 10) + stats.get("atk_bonus", 0) + 200


def find_optimal_intangible_assignment(
    runes: List[Rune],
    base_stats: Dict[str, float],
    constraints: Dict[str, float],
    set_constraints: Dict[str, int],
    objective: str,
    set_bonus_defs: Optional[Dict[int, SetBonusDefinition]] = None
) -> Tuple[Dict[int, int], Dict[str, float], float]:
    """
    Find optimal assignment for multiple intangible runes
    
    Args:
        runes: List of 6 runes (may contain multiple intangible)
        base_stats: Base stats dict
        constraints: Stat constraints
        set_constraints: Set constraints {set_name: count}
        objective: Objective function name
        set_bonus_defs: Optional set bonus definitions
    
    Returns:
        (best_assignment, best_stats, best_score)
        best_assignment: {rune_id: target_set_id}
    """
    intangible_runes = [r for r in runes if r.intangible]
    
    if not intangible_runes:
        # No intangible runes
        stats = calculate_stats(
            runes,
            base_stats.get("base_atk", 900),
            base_stats.get("base_spd", 104),
            base_stats.get("base_hp", 10000),
            base_stats.get("base_def", 500),
            base_stats.get("base_cr", BASE_CR),
            base_stats.get("base_cd", BASE_CD),
            None,
            set_bonus_defs
        )
        score = get_objective_value(objective, stats)
        return {}, stats, score
    
    # Brute force: try all possible assignments
    # Each intangible can be assigned to any set_id or None
    # Limit to reasonable sets (1-25, excluding proc-only sets for assignment)
    assignable_sets = [1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 20, 21]  # Stat-affecting sets
    assignable_sets.append(None)  # "none" option
    
    best_assignment = {}
    best_stats = {}
    best_score = float('-inf')
    
    # Generate all combinations
    from itertools import product
    
    num_intangible = len(intangible_runes)
    for assignment_tuple in product(assignable_sets, repeat=num_intangible):
        assignment = {
            intangible_runes[i].rune_id: assignment_tuple[i]
            for i in range(num_intangible)
            if assignment_tuple[i] is not None
        }
        
        # Calculate stats with this assignment
        stats = calculate_stats(
            runes,
            base_stats.get("base_atk", 900),
            base_stats.get("base_spd", 104),
            base_stats.get("base_hp", 10000),
            base_stats.get("base_def", 500),
            base_stats.get("base_cr", BASE_CR),
            base_stats.get("base_cd", BASE_CD),
            assignment,
            set_bonus_defs
        )
        
        # Check set constraints
        if set_constraints:
            set_counts = count_sets(runes, assignment)
            set_names = {SET_ID_NAME.get(sid, "Unknown"): cnt for sid, cnt in set_counts.items()}
            valid = True
            for set_name, required_count in set_constraints.items():
                if set_names.get(set_name, 0) < required_count:
                    valid = False
                    break
            if not valid:
                continue
        
        # Check stat constraints
        valid = True
        for key, min_val in constraints.items():
            key_upper = key.upper()
            if key_upper == "CR" and stats.get("cr_total", 0) < min_val:
                valid = False
                break
            elif key_upper == "CD" and stats.get("cd_total", 0) < min_val:
                valid = False
                break
            elif key_upper == "SPD" and stats.get("spd_total", 0) < min_val:
                valid = False
                break
            elif key_upper == "ATK_TOTAL" and stats.get("atk_total", 0) < min_val:
                valid = False
                break
            elif key_upper == "HP_TOTAL" and stats.get("hp_total", 0) < min_val:
                valid = False
                break
            elif key_upper == "DEF_TOTAL" and stats.get("def_total", 0) < min_val:
                valid = False
                break
        if not valid:
            continue
        
        # Calculate score
        score = get_objective_value(objective, stats)
        if score > best_score:
            best_score = score
            best_stats = stats
            best_assignment = assignment
    
    return best_assignment, best_stats, best_score


def score_build(
    runes: List[Rune],
    objective: str = "SCORE",
    base_atk: int = 900,
    base_spd: int = 104,
    base_hp: int = 10000,
    base_def: int = 500,
    base_cr: int = BASE_CR,
    base_cd: int = BASE_CD,
    constraints: Dict[str, float] = None,
    set_constraints: Dict[str, int] = None,
    intangible_assignment: Dict[int, int] = None,
    set_bonus_defs: Optional[Dict[int, SetBonusDefinition]] = None
) -> Tuple[float, Dict[str, float], Dict[int, int]]:
    """
    Score a build (supports multiple intangible runes)
    
    Args:
        runes: List of 6 runes
        objective: Objective function name
        base_atk: Base attack
        base_spd: Base speed
        base_hp: Base HP
        base_def: Base defense
        base_cr: Base crit rate
        base_cd: Base crit damage
        constraints: Stat constraints
        set_constraints: Set constraints {set_name: count}
        intangible_assignment: {rune_id: target_set_id} (if None, will optimize)
        set_bonus_defs: Optional set bonus definitions
    
    Returns:
        (score, stats_dict, best_intangible_assignment)
    """
    if len(runes) != 6:
        return 0.0, {}, {}
    
    if constraints is None:
        constraints = {}
    if set_constraints is None:
        set_constraints = {}
    
    base_stats = {
        "base_atk": base_atk,
        "base_spd": base_spd,
        "base_hp": base_hp,
        "base_def": base_def,
        "base_cr": base_cr,
        "base_cd": base_cd,
    }
    
    # Optimize intangible assignment if needed
    if intangible_assignment is None:
        intangible_assignment, stats, score = find_optimal_intangible_assignment(
            runes, base_stats, constraints, set_constraints, objective, set_bonus_defs
        )
    else:
        stats = calculate_stats(
            runes, base_atk, base_spd, base_hp, base_def, base_cr, base_cd,
            intangible_assignment, set_bonus_defs
        )
        score = get_objective_value(objective, stats)
    
    # Check set constraints
    if set_constraints:
        set_counts = count_sets(runes, intangible_assignment)
        set_names = {SET_ID_NAME.get(sid, "Unknown"): cnt for sid, cnt in set_counts.items()}
        for set_name, required_count in set_constraints.items():
            if set_names.get(set_name, 0) < required_count:
                return 0.0, stats, intangible_assignment
    
    # Check stat constraints
    for key, min_val in constraints.items():
        key_upper = key.upper()
        if key_upper == "CR" and stats.get("cr_total", 0) < min_val:
            return 0.0, stats, intangible_assignment
        elif key_upper == "CD" and stats.get("cd_total", 0) < min_val:
            return 0.0, stats, intangible_assignment
        elif key_upper == "SPD" and stats.get("spd_total", 0) < min_val:
            return 0.0, stats, intangible_assignment
        elif key_upper == "ATK_TOTAL" and stats.get("atk_total", 0) < min_val:
            return 0.0, stats, intangible_assignment
        elif key_upper == "HP_TOTAL" and stats.get("hp_total", 0) < min_val:
            return 0.0, stats, intangible_assignment
        elif key_upper == "DEF_TOTAL" and stats.get("def_total", 0) < min_val:
            return 0.0, stats, intangible_assignment
    
    stats["score"] = score
    return score, stats, intangible_assignment
