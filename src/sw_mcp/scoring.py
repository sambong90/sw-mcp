"""빌드 스코어링"""

from typing import List, Tuple, Optional
from .types import Rune, BASE_CR, BASE_CD, RAGE_4SET_CD, FATAL_4SET_ATK_PCT, BLADE_2SET_CR, STAT_ID_NAME


def count_sets(runes: List[Rune], intangible_assignment: str = "none") -> Tuple[int, int, int]:
    """
    세트 개수 계산
    Returns: (rage_or_fatal_count, blade_count, intangible_count)
    """
    rage_or_fatal_count = 0
    blade_count = 0
    intangible_count = 0
    
    for rune in runes:
        if rune.intangible:
            intangible_count += 1
        elif rune.set_id == 5:  # Rage
            rage_or_fatal_count += 1
        elif rune.set_id == 8:  # Fatal
            rage_or_fatal_count += 1
        elif rune.set_id == 4:  # Blade
            blade_count += 1
    
    # 무형 배치 적용
    if intangible_count > 0 and intangible_assignment != "none":
        if intangible_assignment in ["to_Rage", "to_Fatal"]:
            rage_or_fatal_count += intangible_count
        elif intangible_assignment == "to_Blade":
            blade_count += intangible_count
    
    return rage_or_fatal_count, blade_count, intangible_count


def calculate_stats(runes: List[Rune], intangible_assignment: str = "none", base_atk: int = 900) -> dict:
    """스탯 계산"""
    # 기본값
    cr_total = BASE_CR  # 기본 치확 15
    cd_total = BASE_CD  # 기본 치피 50
    atk_pct_total = 0.0
    atk_flat_total = 0.0
    spd_total = 0.0
    
    # 룬 스탯 합산
    for rune in runes:
        # 메인 스탯
        if rune.main_stat_id == 9:  # CR
            cr_total += rune.main_stat_value
        elif rune.main_stat_id == 10:  # CD
            cd_total += rune.main_stat_value
        elif rune.main_stat_id == 4:  # ATK%
            atk_pct_total += rune.main_stat_value
        elif rune.main_stat_id == 3:  # ATK
            atk_flat_total += rune.main_stat_value
        elif rune.main_stat_id == 8:  # SPD
            spd_total += rune.main_stat_value
        
        # prefix_eff 합산
        if rune.has_prefix:
            if rune.prefix_stat_id == 9:  # CR
                cr_total += rune.prefix_stat_value
            elif rune.prefix_stat_id == 10:  # CD
                cd_total += rune.prefix_stat_value
            elif rune.prefix_stat_id == 4:  # ATK%
                atk_pct_total += rune.prefix_stat_value
            elif rune.prefix_stat_id == 3:  # ATK
                atk_flat_total += rune.prefix_stat_value
            elif rune.prefix_stat_id == 8:  # SPD
                spd_total += rune.prefix_stat_value
        
        # 서브 스탯
        for sub in rune.subs:
            if sub.stat_id == 9:  # CR
                cr_total += sub.value
            elif sub.stat_id == 10:  # CD
                cd_total += sub.value
            elif sub.stat_id == 4:  # ATK%
                atk_pct_total += sub.value
            elif sub.stat_id == 3:  # ATK
                atk_flat_total += sub.value
            elif sub.stat_id == 8:  # SPD
                spd_total += sub.value
    
    # 세트 보너스 계산
    rage_or_fatal_count, blade_count, intangible_count = count_sets(runes, intangible_assignment)
    
    # Rage 4세트: CD +40 또는 Fatal 4세트: ATK% +35
    if rage_or_fatal_count >= 4:
        # Rage인지 Fatal인지 확인 (무형 배치 고려)
        has_rage = any(r.set_id == 5 for r in runes)
        has_fatal = any(r.set_id == 8 for r in runes)
        
        # 무형이 Rage/Fatal에 배치된 경우
        if intangible_assignment == "to_Rage":
            has_rage = True
        elif intangible_assignment == "to_Fatal":
            has_fatal = True
        
        # Rage와 Fatal이 모두 있으면 Rage 우선 (일반적으로는 발생하지 않음)
        if has_rage:
            cd_total += RAGE_4SET_CD
        elif has_fatal:
            # Fatal 4세트: ATK% +35
            atk_pct_total += FATAL_4SET_ATK_PCT
    
    # Blade 2세트: CR +12 (2세트 이상일 때)
    if blade_count >= 2:
        cr_total += BLADE_2SET_CR
    
    # 추가 공격력 계산: round(base_atk * (atk_pct_total/100) + atk_flat_total)
    atk_bonus = round(base_atk * (atk_pct_total / 100.0) + atk_flat_total)
    atk_total = base_atk + atk_bonus
    
    return {
        "cr_total": cr_total,
        "cd_total": cd_total,
        "atk_pct_total": atk_pct_total,
        "atk_flat_total": atk_flat_total,
        "atk_bonus": atk_bonus,
        "atk_total": atk_total,
        "spd_total": spd_total,
    }


def score_build(runes: List[Rune], target: str = "B", intangible_assignment: str = "none", 
                base_atk: int = 900) -> Tuple[float, dict]:
    """
    빌드 스코어 계산
    target: "A" (격노+칼날) 또는 "B" (맹공+칼날)
    intangible_assignment: "to_Rage", "to_Fatal", "to_Blade", "none"
    base_atk: 기본 공격력 (기본값 900)
    
    Returns: (score, stats_dict)
    """
    if len(runes) != 6:
        return 0.0, {}
    
    # 무형 룬 최대 1개만 허용
    intangible_count = sum(1 for r in runes if r.intangible)
    if intangible_count > 1:
        return 0.0, {}
    
    # 스탯 계산
    stats = calculate_stats(runes, intangible_assignment, base_atk)
    cr_total = stats["cr_total"]
    cd_total = stats["cd_total"]
    atk_bonus = stats["atk_bonus"]
    
    # 치확 조건 확인 (BASE_CR 15 + Blade 12 + 룬 치확 >= 100)
    if cr_total < 100.0:
        return 0.0, stats
    
    # 세트 조건 확인
    rage_or_fatal_count, blade_count, _ = count_sets(runes, intangible_assignment)
    
    if target == "A":
        # 격노+칼날: Rage 4세트 + Blade 2세트
        if rage_or_fatal_count < 4 or blade_count < 2:
            return 0.0, stats
    elif target == "B":
        # 맹공+칼날: Fatal 4세트 + Blade 2세트
        if rage_or_fatal_count < 4 or blade_count < 2:
            return 0.0, stats
        # Fatal인지 확인 (무형 배치 고려)
        has_fatal = any(r.set_id == 8 for r in runes)
        if not has_fatal and intangible_assignment != "to_Fatal":
            return 0.0, stats
    
    # 스코어 계산: (cd_total * 10) + atk_bonus + 200
    score = (cd_total * 10) + atk_bonus + 200
    
    stats["score"] = score
    stats["intangible_assignment"] = intangible_assignment
    
    return score, stats


def find_best_intangible_assignment(runes: List[Rune], target: str = "B", base_atk: int = 900) -> Tuple[str, float, dict]:
    """
    무형 룬의 최적 배치 찾기
    Returns: (best_assignment, best_score, best_stats)
    """
    intangible_runes = [r for r in runes if r.intangible]
    
    if not intangible_runes:
        # 무형 룬이 없으면 일반 계산
        score, stats = score_build(runes, target, "none", base_atk)
        return "none", score, stats
    
    # 무형 룬이 있으면 배치 옵션 평가 (최대 1개만 허용)
    best_assignment = "none"
    best_score = 0.0
    best_stats = {}
    
    # 옵션 1: Rage/Fatal에 붙이기
    if target == "A":
        assignment = "to_Rage"
    else:  # target == "B"
        assignment = "to_Fatal"
    
    score, stats = score_build(runes, target, assignment, base_atk)
    if score > best_score:
        best_score = score
        best_assignment = assignment
        best_stats = stats
    
    # 옵션 2: Blade에 붙이기
    assignment = "to_Blade"
    score, stats = score_build(runes, target, assignment, base_atk)
    if score > best_score:
        best_score = score
        best_assignment = assignment
        best_stats = stats
    
    # 옵션 3: 무형 없이
    score, stats = score_build(runes, target, "none", base_atk)
    if score > best_score:
        best_score = score
        best_assignment = "none"
        best_stats = stats
    
    return best_assignment, best_score, best_stats

