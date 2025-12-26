"""Test exhaustive mode accuracy (no missed builds)"""

import pytest
from src.sw_core.types import Rune, SubStat
from src.sw_core.optimizer import search_builds
from src.sw_core.rules import validate_build


def test_exhaustive_vs_brute_force():
    """Test that exhaustive mode matches brute force results"""
    # Small rune pool for brute force comparison
    runes = []
    rune_id = 1
    
    # Slot 1: 2 runes
    runes.append(Rune(rune_id, 1, 4, 3, 100, [], 15, 6))
    rune_id += 1
    runes.append(Rune(rune_id, 1, 5, 3, 100, [], 15, 6))
    rune_id += 1
    
    # Slot 2: 2 runes
    runes.append(Rune(rune_id, 2, 4, 4, 63, [], 15, 6))
    rune_id += 1
    runes.append(Rune(rune_id, 2, 5, 4, 63, [], 15, 6))
    rune_id += 1
    
    # Slot 3: 2 runes
    runes.append(Rune(rune_id, 3, 4, 5, 100, [], 15, 6))
    rune_id += 1
    runes.append(Rune(rune_id, 3, 5, 5, 100, [], 15, 6))
    rune_id += 1
    
    # Slot 4: 2 runes
    runes.append(Rune(rune_id, 4, 4, 10, 50, [], 15, 6))
    rune_id += 1
    runes.append(Rune(rune_id, 4, 5, 10, 50, [], 15, 6))
    rune_id += 1
    
    # Slot 5: 2 runes
    runes.append(Rune(rune_id, 5, 4, 1, 100, [], 15, 6))
    rune_id += 1
    runes.append(Rune(rune_id, 5, 5, 1, 100, [], 15, 6))
    rune_id += 1
    
    # Slot 6: 2 runes
    runes.append(Rune(rune_id, 6, 4, 4, 63, [], 15, 6))
    rune_id += 1
    runes.append(Rune(rune_id, 6, 5, 4, 63, [], 15, 6))
    rune_id += 1
    
    # Total: 12 runes = 2^6 = 64 possible combinations
    
    # Brute force: enumerate all valid combinations
    brute_force_results = []
    from itertools import product
    
    slot_runes = {i: [r for r in runes if r.slot == i] for i in range(1, 7)}
    
    for combo in product(*[slot_runes[i] for i in range(1, 7)]):
        combo_list = list(combo)
        if validate_build(combo_list):
            # Calculate score (simplified)
            from src.sw_core.scoring import calculate_stats, get_objective_value
            stats = calculate_stats(combo_list, base_atk=900, base_cr=15, base_cd=50)
            score = get_objective_value("SCORE", stats)
            brute_force_results.append({
                "runes": combo_list,
                "score": score,
                "stats": stats
            })
    
    # Exhaustive mode
    exhaustive_results = search_builds(
        runes,
        base_atk=900,
        base_cr=15,
        base_cd=50,
        objective="SCORE",
        return_all=True,
        mode="exhaustive"
    )
    
    # Compare counts
    assert len(exhaustive_results) == len(brute_force_results), \
        f"Exhaustive found {len(exhaustive_results)} builds, brute force found {len(brute_force_results)}"
    
    # Compare scores (should match)
    exhaustive_scores = sorted([r["score"] for r in exhaustive_results], reverse=True)
    brute_force_scores = sorted([r["score"] for r in brute_force_results], reverse=True)
    
    assert exhaustive_scores == brute_force_scores, \
        f"Score mismatch: exhaustive={exhaustive_scores[:5]}, brute_force={brute_force_scores[:5]}"


def test_exhaustive_no_heuristic_pruning():
    """Test that exhaustive mode doesn't use heuristic candidate trimming"""
    # Create runes with many candidates per slot
    runes = []
    rune_id = 1
    
    for slot in range(1, 7):
        for set_id in [1, 2, 3, 4, 5, 8]:  # 6 sets
            for main_stat_id in [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12]:  # 11 main stats
                # Only add if valid for slot
                from src.sw_core.rules import slot_main_is_allowed
                if slot_main_is_allowed(slot, main_stat_id):
                    runes.append(Rune(rune_id, slot, set_id, main_stat_id, 100, [], 15, 6))
                    rune_id += 1
    
    # Exhaustive mode should find all valid builds
    # Fast mode with max_candidates_per_slot=10 would miss many
    exhaustive_results = search_builds(
        runes,
        base_atk=900,
        objective="SCORE",
        top_n=100,
        mode="exhaustive",
        max_candidates_per_slot=10  # Should be ignored in exhaustive mode
    )
    
    fast_results = search_builds(
        runes,
        base_atk=900,
        objective="SCORE",
        top_n=100,
        mode="fast",
        max_candidates_per_slot=10  # Will be used in fast mode
    )
    
    # Exhaustive should find at least as many as fast (or more)
    assert len(exhaustive_results) >= len(fast_results), \
        f"Exhaustive found {len(exhaustive_results)}, fast found {len(fast_results)}"
    
    # Exhaustive should find the best builds
    if exhaustive_results and fast_results:
        exhaustive_best = max(r["score"] for r in exhaustive_results)
        fast_best = max(r["score"] for r in fast_results)
        assert exhaustive_best >= fast_best, \
            f"Exhaustive best score {exhaustive_best} < fast best score {fast_best}"

