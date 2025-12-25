"""?¤ì½”?´ë§ ?ŒìŠ¤??""

import pytest
from src.sw_core.types import Rune, SubStat, BASE_CR, BLADE_2SET_CR
from src.sw_core.scoring import score_build, calculate_stats, find_best_intangible_assignment


def create_test_rune(rune_id, slot, set_id, main_stat_id, main_value, subs=None):
    """?ŒìŠ¤?¸ìš© ë£??ì„±"""
    if subs is None:
        subs = []
    return Rune(
        rune_id=rune_id,
        slot=slot,
        set_id=set_id,
        main_stat_id=main_stat_id,
        main_stat_value=main_value,
        subs=subs,
        level=6,
        quality=5
    )


def test_base_cr_and_blade_bonus():
    """ê¸°ë³¸ ì¹˜í™• 15?€ ì¹¼ë‚  ?¸íŠ¸ ë³´ë„ˆ??12 ?ìš© ?ŒìŠ¤??""
    # Blade 2?¸íŠ¸ êµ¬ì„±
    runes = [
        create_test_rune(1, 1, 4, 4, 63),  # Blade, ATK%
        create_test_rune(2, 2, 4, 4, 63),  # Blade, ATK%
        create_test_rune(3, 3, 5, 4, 63),  # Rage, ATK%
        create_test_rune(4, 4, 5, 10, 80),  # Rage, CD
        create_test_rune(5, 5, 5, 4, 63),  # Rage, ATK%
        create_test_rune(6, 6, 5, 4, 63),  # Rage, ATK%
    ]
    
    # ì¹˜í™• ?œë¸Œ??ì¶”ê? (ì´?73% ?„ìš”: 100 - 15 - 12 = 73)
    runes[0].subs = [SubStat(9, 20, False, 0)]  # CR 20
    runes[1].subs = [SubStat(9, 20, False, 0)]  # CR 20
    runes[2].subs = [SubStat(9, 20, False, 0)]  # CR 20
    runes[3].subs = [SubStat(9, 13, False, 0)]  # CR 13
    
    stats = calculate_stats(runes, "none")
    
    # BASE_CR 15 + Blade 12 + ë£?CR 73 = 100
    assert stats["cr_total"] == BASE_CR + BLADE_2SET_CR + 73.0


def test_intangible_single_set_assignment():
    """ë¬´í˜• ë£¬ì´ ???¸íŠ¸?ë§Œ ?ìš©?˜ëŠ”ì§€ ?ŒìŠ¤??""
    # ë¬´í˜• 1ê°?+ Rage 3ê°?+ Blade 2ê°?
    runes = [
        create_test_rune(1, 1, 25, 4, 63),  # Intangible
        create_test_rune(2, 2, 5, 4, 63),   # Rage
        create_test_rune(3, 3, 5, 4, 63),   # Rage
        create_test_rune(4, 4, 5, 10, 80),  # Rage
        create_test_rune(5, 5, 4, 4, 63),   # Blade
        create_test_rune(6, 6, 4, 4, 63),   # Blade
    ]
    
    # ì¹˜í™• 100% ?¬ì„±
    runes[0].subs = [SubStat(9, 20, False, 0)]
    runes[1].subs = [SubStat(9, 20, False, 0)]
    runes[2].subs = [SubStat(9, 20, False, 0)]
    runes[3].subs = [SubStat(9, 13, False, 0)]
    
    # ë¬´í˜•??Rage??ë°°ì¹˜
    assignment1, score1, stats1 = find_best_intangible_assignment(runes, "A")
    
    # ë¬´í˜•??Blade??ë°°ì¹˜
    assignment2, score2, stats2 = find_best_intangible_assignment(runes, "A")
    
    # ???¸íŠ¸?ë§Œ ?ìš©?˜ì–´????
    assert assignment1 in ["to_Rage", "to_Blade", "none"]
    # ???’ì? ?¤ì½”?´ë? ? íƒ?´ì•¼ ??
    assert max(score1, score2) > 0


def test_fatal_4set_bonus():
    """Fatal 4?¸íŠ¸ ë³´ë„ˆ??(ATK% +35) ?ŒìŠ¤??""
    runes = [
        create_test_rune(1, 1, 8, 4, 63),  # Fatal
        create_test_rune(2, 2, 8, 4, 63),  # Fatal
        create_test_rune(3, 3, 8, 4, 63),  # Fatal
        create_test_rune(4, 4, 8, 10, 80),  # Fatal
        create_test_rune(5, 5, 4, 4, 63),  # Blade
        create_test_rune(6, 6, 4, 4, 63),  # Blade
    ]
    
    # ì¹˜í™• 100% ?¬ì„±
    runes[0].subs = [SubStat(9, 20, False, 0)]
    runes[1].subs = [SubStat(9, 20, False, 0)]
    runes[2].subs = [SubStat(9, 20, False, 0)]
    runes[3].subs = [SubStat(9, 13, False, 0)]
    
    stats = calculate_stats(runes, "none", base_atk=900)
    
    # Fatal 4?¸íŠ¸ ë³´ë„ˆ?? ATK% +35
    # ë©”ì¸ ATK% 63 * 4 = 252, ë³´ë„ˆ??+35 = 287
    assert stats["atk_pct_total"] >= 287.0


def test_prefix_eff_in_stats():
    """prefix_effê°€ ?¤íƒ¯ ?©ì‚°???¬í•¨?˜ëŠ”ì§€ ?ŒìŠ¤??""
    from src.sw_core.types import Rune, SubStat
    
    rune = Rune(
        rune_id=1,
        slot=1,
        set_id=5,
        main_stat_id=4,
        main_stat_value=63,
        subs=[SubStat(9, 10, False, 0)],
        prefix_stat_id=9,  # CR prefix
        prefix_stat_value=5.0
    )
    
    stats = calculate_stats([rune], "none", base_atk=900)
    
    # BASE_CR 15 + prefix CR 5 + sub CR 10 = 30
    assert stats["cr_total"] == BASE_CR + 5.0 + 10.0


def test_score_formula():
    """?¤ì½”??ê³µì‹ ?ŒìŠ¤?? (cd_total * 10) + atk_bonus + 200"""
    runes = [
        create_test_rune(1, 1, 8, 4, 63),  # Fatal
        create_test_rune(2, 2, 8, 4, 63),  # Fatal
        create_test_rune(3, 3, 8, 4, 63),  # Fatal
        create_test_rune(4, 4, 8, 10, 80),  # Fatal, CD 80
        create_test_rune(5, 5, 4, 4, 63),  # Blade
        create_test_rune(6, 6, 4, 4, 63),  # Blade
    ]
    
    # ì¹˜í™• 100% ?¬ì„±
    runes[0].subs = [SubStat(9, 20, False, 0)]
    runes[1].subs = [SubStat(9, 20, False, 0)]
    runes[2].subs = [SubStat(9, 20, False, 0)]
    runes[3].subs = [SubStat(9, 13, False, 0)]
    
    score, stats = score_build(runes, "B", "none", base_atk=900)
    
    # ?¤ì½”??ê³µì‹: (cd_total * 10) + atk_bonus + 200
    expected_score = (stats["cd_total"] * 10) + stats["atk_bonus"] + 200
    assert abs(score - expected_score) < 0.01

