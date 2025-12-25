"""범용 빌드 스코어링"""

from typing import List, Tuple, Dict, Callable
from .types import Rune, BASE_CR, BASE_CD, STAT_ID_NAME, SET_ID_NAME
from .types import RAGE_4SET_CD, FATAL_4SET_ATK_PCT, BLADE_2SET_CR

# 세트 보너스 매핑
SET_BONUSES = {
    5: {4: 40},  # Rage 4세트: CD +40
    8: {4: 35},  # Fatal 4세트: ATK% +35
    4: {2: 12},  # Blade 2세트: CR +12
}


def count_sets(runes: List[Rune], intangible_assignment: Dict[int, str] = None) -> Dict[int, int]:
    """
    세트 개수 계산 (범용)
    
    Args:
        runes: 룬 리스트
        intangible_assignment: 무형 룬 배치 {rune_id: "to_Rage"/"to_Fatal"/"to_Blade"/"none"}
    
    Returns:
        {set_id: count} 딕셔너리
    """
    if intangible_assignment is None:
        intangible_assignment = {}
    
    set_counts = {}
    intangible_rune_ids = {r.rune_id for r in runes if r.intangible}
    
    for rune in runes:
        if rune.intangible:
            # 무형 룬은 배치에 따라 세트에 추가
            assignment = intangible_assignment.get(rune.rune_id, "none")
            if assignment == "to_Rage":
                set_id = 5
            elif assignment == "to_Fatal":
                set_id = 8
            elif assignment == "to_Blade":
                set_id = 4
            else:
                continue  # "none"이면 세트에 추가 안 함
        else:
            set_id = rune.set_id
        
        set_counts[set_id] = set_counts.get(set_id, 0) + 1
    
    return set_counts


def calculate_stats(runes: List[Rune], 
                   base_atk: int = 900,
                   base_spd: int = 104,
                   base_hp: int = 10000,
                   base_def: int = 500,
                   intangible_assignment: Dict[int, str] = None) -> Dict[str, float]:
    """
    범용 스탯 계산 (모든 스탯 포함)
    
    Args:
        runes: 룬 리스트
        base_atk: 기본 공격력
        base_spd: 기본 속도
        base_hp: 기본 체력
        base_def: 기본 방어력
        intangible_assignment: 무형 룬 배치
    
    Returns:
        모든 스탯을 포함한 딕셔너리
    """
    if intangible_assignment is None:
        intangible_assignment = {}
    
    # 기본값
    stats = {
        "cr_total": BASE_CR,  # 기본 치확 15
        "cd_total": BASE_CD,  # 기본 치피 50
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
    
    # 룬 스탯 합산
    for rune in runes:
        # 메인 스탯
        if rune.main_stat_id == 1:  # HP
            stats["hp_flat_total"] += rune.main_stat_value
        elif rune.main_stat_id == 2:  # HP%
            stats["hp_pct_total"] += rune.main_stat_value
        elif rune.main_stat_id == 3:  # ATK
            stats["atk_flat_total"] += rune.main_stat_value
        elif rune.main_stat_id == 4:  # ATK%
            stats["atk_pct_total"] += rune.main_stat_value
        elif rune.main_stat_id == 5:  # DEF
            stats["def_flat_total"] += rune.main_stat_value
        elif rune.main_stat_id == 6:  # DEF%
            stats["def_pct_total"] += rune.main_stat_value
        elif rune.main_stat_id == 8:  # SPD
            stats["spd_total"] += rune.main_stat_value
        elif rune.main_stat_id == 9:  # CR
            stats["cr_total"] += rune.main_stat_value
        elif rune.main_stat_id == 10:  # CD
            stats["cd_total"] += rune.main_stat_value
        elif rune.main_stat_id == 11:  # RES
            stats["res_total"] += rune.main_stat_value
        elif rune.main_stat_id == 12:  # ACC
            stats["acc_total"] += rune.main_stat_value
        
        # prefix_eff 합산
        if rune.has_prefix:
            if rune.prefix_stat_id == 1:
                stats["hp_flat_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 2:
                stats["hp_pct_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 3:
                stats["atk_flat_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 4:
                stats["atk_pct_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 5:
                stats["def_flat_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 6:
                stats["def_pct_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 8:
                stats["spd_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 9:
                stats["cr_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 10:
                stats["cd_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 11:
                stats["res_total"] += rune.prefix_stat_value
            elif rune.prefix_stat_id == 12:
                stats["acc_total"] += rune.prefix_stat_value
        
        # 서브 스탯
        for sub in rune.subs:
            if sub.stat_id == 1:
                stats["hp_flat_total"] += sub.value
            elif sub.stat_id == 2:
                stats["hp_pct_total"] += sub.value
            elif sub.stat_id == 3:
                stats["atk_flat_total"] += sub.value
            elif sub.stat_id == 4:
                stats["atk_pct_total"] += sub.value
            elif sub.stat_id == 5:
                stats["def_flat_total"] += sub.value
            elif sub.stat_id == 6:
                stats["def_pct_total"] += sub.value
            elif sub.stat_id == 8:
                stats["spd_total"] += sub.value
            elif sub.stat_id == 9:
                stats["cr_total"] += sub.value
            elif sub.stat_id == 10:
                stats["cd_total"] += sub.value
            elif sub.stat_id == 11:
                stats["res_total"] += sub.value
            elif sub.stat_id == 12:
                stats["acc_total"] += sub.value
    
    # 세트 보너스 계산
    set_counts = count_sets(runes, intangible_assignment)
    for set_id, count in set_counts.items():
        if set_id in SET_BONUSES:
            bonuses = SET_BONUSES[set_id]
            for threshold, bonus in bonuses.items():
                if count >= threshold:
                    if set_id == 5:  # Rage 4세트: CD +40
                        stats["cd_total"] += bonus
                    elif set_id == 8:  # Fatal 4세트: ATK% +35
                        stats["atk_pct_total"] += bonus
                    elif set_id == 4:  # Blade 2세트: CR +12
                        stats["cr_total"] += bonus
    
    # 총합 계산
    atk_bonus = round(base_atk * (stats["atk_pct_total"] / 100.0) + stats["atk_flat_total"])
    stats["atk_total"] = base_atk + atk_bonus
    stats["atk_bonus"] = atk_bonus
    
    hp_bonus = round(base_hp * (stats["hp_pct_total"] / 100.0) + stats["hp_flat_total"])
    stats["hp_total"] = base_hp + hp_bonus
    stats["hp_bonus"] = hp_bonus
    
    def_bonus = round(base_def * (stats["def_pct_total"] / 100.0) + stats["def_flat_total"])
    stats["def_total"] = base_def + def_bonus
    stats["def_bonus"] = def_bonus
    
    stats["spd_total"] = base_spd + stats["spd_total"]
    
    return stats


# Objective 함수들 (플러그인 형태)
OBJECTIVE_FUNCTIONS: Dict[str, Callable[[Dict[str, float]], float]] = {}


def register_objective(name: str, func: Callable[[Dict[str, float]], float]):
    """Objective 함수 등록"""
    OBJECTIVE_FUNCTIONS[name] = func


def get_objective_value(objective: str, stats: Dict[str, float]) -> float:
    """
    Objective 값 계산
    
    Args:
        objective: Objective 이름 ("SCORE", "ATK_TOTAL", "EHP", "SPD" 등)
        stats: 스탯 딕셔너리
    
    Returns:
        Objective 값
    """
    if objective in OBJECTIVE_FUNCTIONS:
        return OBJECTIVE_FUNCTIONS[objective](stats)
    
    # 기본 objective들
    if objective == "SCORE":
        # 루쉔 스코어: (cd_total * 10) + atk_bonus + 200
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
        # 대미지 프록시: ATK * (1 + CD/100) * (1 + CR/100)
        atk = stats.get("atk_total", 0)
        cd = stats.get("cd_total", 0)
        cr = min(stats.get("cr_total", 0), 100.0)  # CR은 100% 제한
        return atk * (1 + cd / 100.0) * (1 + cr / 100.0)
    else:
        # 기본값: SCORE
        return (stats.get("cd_total", 0) * 10) + stats.get("atk_bonus", 0) + 200


def score_build(runes: List[Rune],
                objective: str = "SCORE",
                base_atk: int = 900,
                base_spd: int = 104,
                base_hp: int = 10000,
                base_def: int = 500,
                constraints: Dict[str, float] = None,
                set_constraints: Dict[str, int] = None,
                intangible_assignment: Dict[int, str] = None) -> Tuple[float, Dict[str, float], Dict[int, str]]:
    """
    범용 빌드 스코어 계산
    
    Args:
        runes: 룬 리스트
        objective: 목표 함수 ("SCORE", "ATK_TOTAL", "EHP", "SPD" 등)
        base_atk: 기본 공격력
        base_spd: 기본 속도
        base_hp: 기본 체력
        base_def: 기본 방어력
        constraints: 제약조건 ({"CR": 100, "SPD": 100} 등)
        set_constraints: 세트 제약조건 ({"Rage": 4, "Blade": 2} 등)
        intangible_assignment: 무형 룬 배치
    
    Returns:
        (score, stats_dict, best_intangible_assignment)
    """
    if len(runes) != 6:
        return 0.0, {}, {}
    
    if constraints is None:
        constraints = {}
    if set_constraints is None:
        set_constraints = {}
    if intangible_assignment is None:
        intangible_assignment = {}
    
    # 무형 룬 최대 1개만 허용
    intangible_count = sum(1 for r in runes if r.intangible)
    if intangible_count > 1:
        return 0.0, {}, {}
    
    # 무형 룬 배치 최적화 (set_constraints가 있을 때만)
    best_intangible_assignment = {}
    if intangible_count > 0 and set_constraints:
        best_score = 0.0
        best_stats = {}
        
        # 무형 룬 ID 찾기
        intangible_rune = next((r for r in runes if r.intangible), None)
        if intangible_rune:
            # 배치 옵션 평가
            for assignment in ["to_Rage", "to_Fatal", "to_Blade", "none"]:
                test_assignment = {intangible_rune.rune_id: assignment}
                stats = calculate_stats(runes, base_atk, base_spd, base_hp, base_def, test_assignment)
                
                # 세트 제약조건 확인
                if set_constraints:
                    set_counts = count_sets(runes, test_assignment)
                    set_names = {SET_ID_NAME.get(sid, "Unknown"): cnt for sid, cnt in set_counts.items()}
                    valid = True
                    for set_name, required_count in set_constraints.items():
                        if set_names.get(set_name, 0) < required_count:
                            valid = False
                            break
                    if not valid:
                        continue
                
                # 제약조건 확인
                valid = True
                for key, min_val in constraints.items():
                    if key.upper() == "CR" and stats.get("cr_total", 0) < min_val:
                        valid = False
                        break
                    elif key.upper() == "CD" and stats.get("cd_total", 0) < min_val:
                        valid = False
                        break
                    elif key.upper() == "SPD" and stats.get("spd_total", 0) < min_val:
                        valid = False
                        break
                    elif key.upper() == "ATK_TOTAL" and stats.get("atk_total", 0) < min_val:
                        valid = False
                        break
                    elif key.upper() == "HP_TOTAL" and stats.get("hp_total", 0) < min_val:
                        valid = False
                        break
                    elif key.upper() == "DEF_TOTAL" and stats.get("def_total", 0) < min_val:
                        valid = False
                        break
                if not valid:
                    continue
                
                score = get_objective_value(objective, stats)
                if score > best_score:
                    best_score = score
                    best_stats = stats
                    best_intangible_assignment = test_assignment
    else:
        # 무형 룬이 없거나 set_constraints가 없으면 일반 계산
        stats = calculate_stats(runes, base_atk, base_spd, base_hp, base_def, intangible_assignment)
        best_stats = stats
        best_intangible_assignment = intangible_assignment
    
    # 세트 제약조건 확인
    if set_constraints:
        set_counts = count_sets(runes, best_intangible_assignment)
        set_names = {SET_ID_NAME.get(sid, "Unknown"): cnt for sid, cnt in set_counts.items()}
        for set_name, required_count in set_constraints.items():
            if set_names.get(set_name, 0) < required_count:
                return 0.0, best_stats, best_intangible_assignment
    
    # 제약조건 확인
    for key, min_val in constraints.items():
        key_upper = key.upper()
        if key_upper == "CR" and best_stats.get("cr_total", 0) < min_val:
            return 0.0, best_stats, best_intangible_assignment
        elif key_upper == "CD" and best_stats.get("cd_total", 0) < min_val:
            return 0.0, best_stats, best_intangible_assignment
        elif key_upper == "SPD" and best_stats.get("spd_total", 0) < min_val:
            return 0.0, best_stats, best_intangible_assignment
        elif key_upper == "ATK_TOTAL" and best_stats.get("atk_total", 0) < min_val:
            return 0.0, best_stats, best_intangible_assignment
        elif key_upper == "HP_TOTAL" and best_stats.get("hp_total", 0) < min_val:
            return 0.0, best_stats, best_intangible_assignment
        elif key_upper == "DEF_TOTAL" and best_stats.get("def_total", 0) < min_val:
            return 0.0, best_stats, best_intangible_assignment
    
    # Objective 값 계산
    score = get_objective_value(objective, best_stats)
    best_stats["score"] = score
    
    return score, best_stats, best_intangible_assignment
