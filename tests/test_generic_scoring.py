"""Test generic scoring for ALL rune sets"""

import pytest
from src.sw_core.types import Rune, SubStat
from src.sw_core.scoring import calculate_stats, score_build, count_sets
from src.sw_core.set_bonuses import SET_BONUS_DEFINITIONS


def test_blade_2set_cr_bonus():
    """Test Blade 2-set CR +12 bonus"""
    r1 = Rune(1, 1, 4, 3, 100, [], 15, 6)  # Slot 1, Blade, ATK flat
    r2 = Rune(2, 2, 4, 4, 63, [], 15, 6)  # Slot 2, Blade, ATK%
    
    stats = calculate_stats([r1, r2], base_atk=900, base_cr=15)
    assert stats["cr_total"] == 15 + 12  # Base CR + Blade 2-set bonus


def test_rage_4set_cd_bonus():
    """Test Rage 4-set CD +40 bonus"""
    runes = [
        Rune(i, i, 5, 1 if i == 5 else 2, 100 if i == 5 else 63, [], 15, 6)
        for i in range(1, 5)
    ]  # 4 Rage runes
    
    stats = calculate_stats(runes, base_atk=900, base_cd=50)
    assert stats["cd_total"] == 50 + 40  # Base CD + Rage 4-set bonus


def test_fatal_4set_atk_pct_bonus():
    """Test Fatal 4-set ATK% +35 bonus"""
    runes = [
        Rune(i, i, 8, 1 if i == 5 else 2, 100 if i == 5 else 63, [], 15, 6)
        for i in range(1, 5)
    ]  # 4 Fatal runes
    
    stats = calculate_stats(runes, base_atk=900)
    assert stats["atk_pct_total"] == 35.0  # Fatal 4-set bonus
    assert stats["atk_total"] == 900 + int(900 * (35.0 / 100.0))  # base + bonus


def test_swift_2set_spd_pct_bonus():
    """Test Swift 2-set SPD% bonus (applies to base SPD)"""
    r1 = Rune(1, 1, 3, 3, 100, [], 15, 6)  # Slot 1, Swift, ATK flat
    r2 = Rune(2, 2, 3, 4, 63, [], 15, 6)  # Slot 2, Swift, ATK%
    
    stats = calculate_stats([r1, r2], base_atk=900, base_spd=104)
    # Swift 2-set: +25% to base SPD
    expected_spd = 104 + int(104 * (25.0 / 100.0))
    assert stats["spd_total"] == expected_spd


def test_multiple_intangible_assignment():
    """Test multiple intangible runes assignment"""
    # 2 intangible runes + 4 Blade runes
    runes = [
        Rune(1, 1, 25, 3, 100, [], 15, 6),  # Intangible
        Rune(2, 2, 25, 4, 63, [], 15, 6),  # Intangible
        Rune(3, 3, 4, 5, 100, [], 15, 6),  # Blade
        Rune(4, 4, 4, 6, 63, [], 15, 6),  # Blade
        Rune(5, 5, 4, 1, 100, [], 15, 6),  # Blade
        Rune(6, 6, 4, 2, 63, [], 15, 6),  # Blade
    ]
    
    # Assign both intangible to Blade to get 6 Blade (3 sets of 2)
    assignment = {1: 4, 2: 4}  # Both to Blade (set_id=4)
    set_counts = count_sets(runes, assignment)
    assert set_counts[4] == 6  # 4 Blade + 2 Intangible assigned to Blade
    
    stats = calculate_stats(runes, base_atk=900, base_cr=15, intangible_assignment=assignment)
    # Blade 2-set bonus: 6 runes = 3 pairs, but bonus applies once per 2-set threshold
    # With 6 Blade runes, we have count=6, which is >= 2, so bonus applies once
    # (Set bonuses don't stack - they're thresholds, not multipliers)
    assert stats["cr_total"] == 15 + 12  # Base CR + Blade 2-set bonus (once)


def test_energy_2set_hp_pct_bonus():
    """Test Energy 2-set HP% +15 bonus"""
    r1 = Rune(1, 1, 1, 3, 100, [], 15, 6)  # Slot 1, Energy, ATK flat
    r2 = Rune(2, 2, 1, 4, 63, [], 15, 6)  # Slot 2, Energy, ATK%
    
    stats = calculate_stats([r1, r2], base_atk=900, base_hp=10000)
    assert stats["hp_pct_total"] == 15.0  # Energy 2-set bonus
    assert stats["hp_total"] == 10000 + int(10000 * (15.0 / 100.0))


def test_guard_2set_def_pct_bonus():
    """Test Guard 2-set DEF% +15 bonus"""
    r1 = Rune(1, 1, 2, 3, 100, [], 15, 6)  # Slot 1, Guard, ATK flat
    r2 = Rune(2, 2, 2, 4, 63, [], 15, 6)  # Slot 2, Guard, ATK%
    
    stats = calculate_stats([r1, r2], base_atk=900, base_def=500)
    assert stats["def_pct_total"] == 15.0  # Guard 2-set bonus
    assert stats["def_total"] == 500 + int(500 * (15.0 / 100.0))


def test_proc_sets_no_stat_bonus():
    """Test that proc sets (Violent/Will/etc) don't add stat bonuses"""
    r1 = Rune(1, 1, 11, 3, 100, [], 15, 6)  # Slot 1, Violent, ATK flat
    r2 = Rune(2, 2, 11, 4, 63, [], 15, 6)  # Slot 2, Violent, ATK%
    
    stats = calculate_stats([r1, r2], base_atk=900, base_cr=15)
    # Violent is a proc set, should not add stat bonuses
    # But rune main stats still apply (r2 has ATK% main stat)
    assert stats["cr_total"] == 15  # No CR bonus from Violent
    assert stats["atk_pct_total"] == 63.0  # From r2's main stat (ATK%), not from set bonus


def test_score_build_with_intangible_optimization():
    """Test score_build optimizes intangible assignment"""
    # 1 intangible + 3 Rage + 2 Blade
    runes = [
        Rune(1, 1, 25, 3, 100, [], 15, 6),  # Intangible
        Rune(2, 2, 5, 4, 63, [], 15, 6),  # Rage
        Rune(3, 3, 5, 5, 100, [], 15, 6),  # Rage
        Rune(4, 4, 5, 6, 63, [], 15, 6),  # Rage
        Rune(5, 5, 4, 1, 100, [], 15, 6),  # Blade
        Rune(6, 6, 4, 2, 63, [], 15, 6),  # Blade
    ]
    
    set_constraints = {"Rage": 4, "Blade": 2}
    
    score, stats, assignment = score_build(
        runes,
        objective="SCORE",
        base_atk=900,
        base_cr=15,
        base_cd=50,
        set_constraints=set_constraints
    )
    
    # Intangible should be assigned to Rage to satisfy Rage 4-set
    assert assignment.get(1) == 5  # Intangible assigned to Rage (set_id=5)
    assert stats["cd_total"] >= 50 + 40  # Rage 4-set bonus applied
    assert stats["cr_total"] >= 15 + 12  # Blade 2-set bonus applied

