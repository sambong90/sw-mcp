"""루쉔 최적화"""

from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from .types import Rune, STAT_ID_NAME, BASE_CR, BASE_CD
from .scoring import score_build, find_best_intangible_assignment, calculate_stats


def filter_rune_by_slot(runes: List[Rune], slot: int, target: str = "B", 
                        allow_any_main: bool = False) -> List[Rune]:
    """
    슬롯별 룬 필터링 및 조건 검사
    
    Args:
        runes: 전체 룬 리스트
        slot: 슬롯 번호 (1-6)
        target: "A" 또는 "B" (사용 안 함, 호환성 유지)
        allow_any_main: True면 메인스탯 제한 없음 (preset 해제)
    
    Returns:
        필터링된 룬 리스트
    """
    filtered = [r for r in runes if r.slot == slot]
    
    if slot == 1:
        # 슬롯1: 서브옵에 DEF%, DEF+ 금지 (서브/보석 포함)
        filtered = [r for r in filtered if not r.has_sub_stat(6)]  # DEF% 서브옵 제거
        filtered = [r for r in filtered if not r.has_sub_stat(5)]  # DEF+ 서브옵 제거
        # prefix도 체크
        filtered = [r for r in filtered if not (r.has_prefix and r.prefix_stat_id in [5, 6])]
    elif slot == 2:
        # 슬롯2: 메인 ATK%만 허용 (preset 해제 시 모든 메인 허용)
        if not allow_any_main:
            filtered = [r for r in filtered if r.main_stat_id == 4]  # ATK%
    elif slot == 3:
        # 슬롯3: 서브옵에 ATK% 금지, ATK+도 금지 (서브/보석 포함)
        filtered = [r for r in filtered if not r.has_sub_stat(4)]  # ATK% 서브옵 제거
        filtered = [r for r in filtered if not r.has_sub_stat(3)]  # ATK+ 서브옵 제거
        # prefix도 체크
        filtered = [r for r in filtered if not (r.has_prefix and r.prefix_stat_id in [3, 4])]
    elif slot == 4:
        # 슬롯4: 메인 CD만 허용 (preset 해제 시 모든 메인 허용)
        if not allow_any_main:
            filtered = [r for r in filtered if r.main_stat_id == 10]  # CD
    elif slot == 6:
        # 슬롯6: 메인 ATK%만 허용 (preset 해제 시 모든 메인 허용)
        if not allow_any_main:
            filtered = [r for r in filtered if r.main_stat_id == 4]  # ATK%
    
    return filtered


class DPState:
    """DP 상태"""
    def __init__(self, count_rage: int = 0, count_fatal: int = 0, count_blade: int = 0,
                 count_intangible: int = 0, cr: float = 0.0, cd: float = 0.0,
                 atk_pct: float = 0.0, atk_flat: float = 0.0, spd: float = 0.0,
                 rune_ids: Tuple[int, ...] = ()):
        self.count_rage = count_rage
        self.count_fatal = count_fatal
        self.count_blade = count_blade
        self.count_intangible = count_intangible
        self.cr = cr
        self.cd = cd
        self.atk_pct = atk_pct
        self.atk_flat = atk_flat
        self.spd = spd
        self.rune_ids = rune_ids
    
    def __hash__(self):
        return hash((self.count_rage, self.count_fatal, self.count_blade, 
                    self.count_intangible, self.rune_ids))
    
    def __eq__(self, other):
        if not isinstance(other, DPState):
            return False
        return (self.count_rage == other.count_rage and
                self.count_fatal == other.count_fatal and
                self.count_blade == other.count_blade and
                self.count_intangible == other.count_intangible and
                self.rune_ids == other.rune_ids)
    
    def add_rune(self, rune: Rune) -> 'DPState':
        """룬 추가하여 새 상태 생성"""
        new_count_rage = self.count_rage
        new_count_fatal = self.count_fatal
        new_count_blade = self.count_blade
        new_count_intangible = self.count_intangible
        
        if rune.intangible:
            new_count_intangible += 1
        elif rune.set_id == 5:  # Rage
            new_count_rage += 1
        elif rune.set_id == 8:  # Fatal
            new_count_fatal += 1
        elif rune.set_id == 4:  # Blade
            new_count_blade += 1
        
        # 스탯 추가
        new_cr = self.cr
        new_cd = self.cd
        new_atk_pct = self.atk_pct
        new_atk_flat = self.atk_flat
        new_spd = self.spd
        
        # 메인 스탯
        if rune.main_stat_id == 9:  # CR
            new_cr += rune.main_stat_value
        elif rune.main_stat_id == 10:  # CD
            new_cd += rune.main_stat_value
        elif rune.main_stat_id == 4:  # ATK%
            new_atk_pct += rune.main_stat_value
        elif rune.main_stat_id == 3:  # ATK
            new_atk_flat += rune.main_stat_value
        elif rune.main_stat_id == 8:  # SPD
            new_spd += rune.main_stat_value
        
        # prefix_eff
        if rune.has_prefix:
            if rune.prefix_stat_id == 9:  # CR
                new_cr += rune.prefix_stat_value
            elif rune.prefix_stat_id == 10:  # CD
                new_cd += rune.prefix_stat_value
            elif rune.prefix_stat_id == 4:  # ATK%
                new_atk_pct += rune.prefix_stat_value
            elif rune.prefix_stat_id == 3:  # ATK
                new_atk_flat += rune.prefix_stat_value
            elif rune.prefix_stat_id == 8:  # SPD
                new_spd += rune.prefix_stat_value
        
        # 서브 스탯
        for sub in rune.subs:
            if sub.stat_id == 9:  # CR
                new_cr += sub.value
            elif sub.stat_id == 10:  # CD
                new_cd += sub.value
            elif sub.stat_id == 4:  # ATK%
                new_atk_pct += sub.value
            elif sub.stat_id == 3:  # ATK
                new_atk_flat += sub.value
            elif sub.stat_id == 8:  # SPD
                new_spd += sub.value
        
        new_rune_ids = self.rune_ids + (rune.rune_id,)
        
        return DPState(
            count_rage=new_count_rage,
            count_fatal=new_count_fatal,
            count_blade=new_count_blade,
            count_intangible=new_count_intangible,
            cr=new_cr,
            cd=new_cd,
            atk_pct=new_atk_pct,
            atk_flat=new_atk_flat,
            spd=new_spd,
            rune_ids=new_rune_ids
        )


def calculate_max_remaining_sets(slot_runes: Dict[int, List[Rune]], start_slot: int) -> Dict[str, int]:
    """남은 슬롯에서 얻을 수 있는 최대 세트 개수 계산 (pruning용)"""
    max_sets = {
        "RAGE": 0,
        "FATAL": 0,
        "BLADE": 0,
        "INTANGIBLE": 0,
    }
    
    for slot in range(start_slot, 7):
        if slot not in slot_runes:
            continue
        
        slot_max = {
            "RAGE": 0,
            "FATAL": 0,
            "BLADE": 0,
            "INTANGIBLE": 0,
        }
        
        for rune in slot_runes[slot]:
            if rune.intangible:
                slot_max["INTANGIBLE"] = max(slot_max["INTANGIBLE"], 1)
            elif rune.set_id == 5:  # Rage
                slot_max["RAGE"] = max(slot_max["RAGE"], 1)
            elif rune.set_id == 8:  # Fatal
                slot_max["FATAL"] = max(slot_max["FATAL"], 1)
            elif rune.set_id == 4:  # Blade
                slot_max["BLADE"] = max(slot_max["BLADE"], 1)
        
        # 각 슬롯의 최대값을 합산 (슬롯당 최대 1개씩)
        for key in max_sets:
            max_sets[key] += slot_max[key]
    
    return max_sets


def calculate_heuristic_score(state: DPState, base_atk: int = 900) -> float:
    """휴리스틱 스코어 계산 (상위 K개 유지용)"""
    # 간단한 휴리스틱: ATK%와 CD에 가중치 부여
    # 실제 스코어 공식과 유사하게: (cd * 10) + atk_bonus + 200
    atk_bonus_heuristic = state.atk_pct * (base_atk / 100.0) + state.atk_flat
    score_heuristic = (state.cd * 10) + atk_bonus_heuristic + 200
    return score_heuristic


def calculate_max_remaining_stats(slot_runes: Dict[int, List[Rune]], start_slot: int) -> Dict[str, float]:
    """남은 슬롯에서 얻을 수 있는 최대 스탯 계산 (pruning용)"""
    max_stats = {
        "CR": 0.0,
        "CD": 0.0,
        "ATK_PCT": 0.0,
        "ATK_FLAT": 0.0,
        "SPD": 0.0,
    }
    
    for slot in range(start_slot, 7):
        if slot not in slot_runes:
            continue
        
        slot_max = {
            "CR": 0.0,
            "CD": 0.0,
            "ATK_PCT": 0.0,
            "ATK_FLAT": 0.0,
            "SPD": 0.0,
        }
        
        for rune in slot_runes[slot]:
            # 메인 스탯
            if rune.main_stat_id == 9:  # CR
                slot_max["CR"] = max(slot_max["CR"], rune.main_stat_value)
            elif rune.main_stat_id == 10:  # CD
                slot_max["CD"] = max(slot_max["CD"], rune.main_stat_value)
            elif rune.main_stat_id == 4:  # ATK%
                slot_max["ATK_PCT"] = max(slot_max["ATK_PCT"], rune.main_stat_value)
            elif rune.main_stat_id == 3:  # ATK
                slot_max["ATK_FLAT"] = max(slot_max["ATK_FLAT"], rune.main_stat_value)
            elif rune.main_stat_id == 8:  # SPD
                slot_max["SPD"] = max(slot_max["SPD"], rune.main_stat_value)
            
            # prefix
            if rune.has_prefix:
                if rune.prefix_stat_id == 9:
                    slot_max["CR"] = max(slot_max["CR"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 10:
                    slot_max["CD"] = max(slot_max["CD"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 4:
                    slot_max["ATK_PCT"] = max(slot_max["ATK_PCT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 3:
                    slot_max["ATK_FLAT"] = max(slot_max["ATK_FLAT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 8:
                    slot_max["SPD"] = max(slot_max["SPD"], rune.prefix_stat_value)
            
            # 서브 스탯
            for sub in rune.subs:
                if sub.stat_id == 9:
                    slot_max["CR"] = max(slot_max["CR"], sub.value)
                elif sub.stat_id == 10:
                    slot_max["CD"] = max(slot_max["CD"], sub.value)
                elif sub.stat_id == 4:
                    slot_max["ATK_PCT"] = max(slot_max["ATK_PCT"], sub.value)
                elif sub.stat_id == 3:
                    slot_max["ATK_FLAT"] = max(slot_max["ATK_FLAT"], sub.value)
                elif sub.stat_id == 8:
                    slot_max["SPD"] = max(slot_max["SPD"], sub.value)
        
        # 각 슬롯의 최대값을 합산
        for key in max_stats:
            max_stats[key] += slot_max[key]
    
    return max_stats


def check_set_requirements(state: DPState, slot_runes: Dict[int, List[Rune]], 
                          current_slot: int, target: str, require_sets: bool = True) -> bool:
    """세트 요구사항을 만족할 수 있는지 확인 (pruning)"""
    if not require_sets:
        return True  # 세트 조건 체크 안 함
    
    remaining_slots = 6 - current_slot
    
    # 남은 슬롯에서 얻을 수 있는 최대 세트 개수
    max_remaining_sets = calculate_max_remaining_sets(slot_runes, current_slot + 1)
    
    if target == "A":
        # A: Rage >= 4 AND Blade >= 2
        # Rage 조건: 현재 Rage + 무형(Blade에 안 붙일 경우) + 남은 최대 Rage/무형
        max_rage_with_intangible = state.count_rage + state.count_intangible + max_remaining_sets["RAGE"] + max_remaining_sets["INTANGIBLE"]
        if max_rage_with_intangible < 4:
            return False
        
        # Blade 조건: 현재 Blade + 무형(Blade에 붙일 경우) + 남은 최대 Blade
        max_blade_with_intangible = state.count_blade + state.count_intangible + max_remaining_sets["BLADE"] + max_remaining_sets["INTANGIBLE"]
        if max_blade_with_intangible < 2:
            return False
    else:  # target == "B"
        # B: Fatal >= 4 AND Blade >= 2
        # Fatal 조건: 현재 Fatal + 무형(Fatal에 붙일 경우) + 남은 최대 Fatal/무형
        max_fatal_with_intangible = state.count_fatal + state.count_intangible + max_remaining_sets["FATAL"] + max_remaining_sets["INTANGIBLE"]
        if max_fatal_with_intangible < 4:
            return False
        
        # Blade 조건: 현재 Blade + 무형(Blade에 붙일 경우) + 남은 최대 Blade
        max_blade_with_intangible = state.count_blade + state.count_intangible + max_remaining_sets["BLADE"] + max_remaining_sets["INTANGIBLE"]
        if max_blade_with_intangible < 2:
            return False
    
    return True


def check_constraints(state: DPState, constraints: Dict[str, float], 
                     slot_runes: Dict[int, List[Rune]], current_slot: int,
                     base_atk: int, base_spd: int, target: str = "B",
                     require_sets: bool = True) -> bool:
    """제약 조건을 만족할 수 있는지 확인 (pruning)"""
    # 세트 요구사항 체크
    if not check_set_requirements(state, slot_runes, current_slot, target, require_sets):
        return False
    
    if not constraints:
        return True
    
    # 현재까지의 스탯 (기본값 포함)
    current_cr = BASE_CR + state.cr
    current_cd = BASE_CD + state.cd
    current_spd = base_spd + state.spd
    
    # 남은 슬롯에서 얻을 수 있는 최대 스탯
    max_remaining = calculate_max_remaining_stats(slot_runes, current_slot + 1)
    
    # 남은 슬롯에서 얻을 수 있는 최대 세트 개수
    max_remaining_sets = calculate_max_remaining_sets(slot_runes, current_slot + 1)
    remaining_slots = 6 - current_slot
    
    # 세트 보너스 고려 (최선의 경우 가정)
    # Blade 2세트 보너스 CR +12
    potential_blade_count = state.count_blade + max_remaining_sets["BLADE"] + (state.count_intangible if state.count_intangible > 0 else 0)
    if potential_blade_count >= 2:
        current_cr += 12
    
    # Rage/Fatal 4세트 보너스 (최선의 경우)
    if target == "A":
        potential_rage_count = state.count_rage + max_remaining_sets["RAGE"] + (state.count_intangible if state.count_intangible > 0 else 0)
        if potential_rage_count >= 4:
            # Rage 4세트: CD +40
            current_cd += 40
    else:
        potential_fatal_count = state.count_fatal + max_remaining_sets["FATAL"] + (state.count_intangible if state.count_intangible > 0 else 0)
        if potential_fatal_count >= 4:
            # Fatal 4세트: ATK% +35
            max_remaining["ATK_PCT"] += 35
    
    # 최종 예상 스탯
    final_cr = current_cr + max_remaining["CR"]
    final_cd = current_cd + max_remaining["CD"]
    final_spd = current_spd + max_remaining["SPD"]
    
    # ATK_BONUS와 ATK_TOTAL 계산
    final_atk_pct = state.atk_pct + max_remaining["ATK_PCT"]
    final_atk_flat = state.atk_flat + max_remaining["ATK_FLAT"]
    final_atk_bonus = round(base_atk * (final_atk_pct / 100.0) + final_atk_flat)
    final_atk_total = base_atk + final_atk_bonus
    
    # 제약 조건 체크
    if "CR" in constraints and final_cr < constraints["CR"]:
        return False
    if "CD" in constraints and final_cd < constraints["CD"]:
        return False
    if "SPD" in constraints and final_spd < constraints["SPD"]:
        return False
    if "ATK_BONUS" in constraints and final_atk_bonus < constraints["ATK_BONUS"]:
        return False
    if "ATK_TOTAL" in constraints and final_atk_total < constraints["ATK_TOTAL"]:
        return False
    if "ATK_PCT" in constraints and final_atk_pct < constraints["ATK_PCT"]:
        return False
    if "ATK_FLAT" in constraints and final_atk_flat < constraints["ATK_FLAT"]:
        return False
    
    return True


def optimize_lushen(runes: List[Rune], target: str = "B", 
                    gem_mode: str = "none", grind_mode: str = "none",
                    top_n: int = 10, base_atk: int = 900,
                    max_candidates_per_slot: int = 300,
                    mode: str = "exhaustive") -> List[Dict]:
    """
    루쉔 최적화
    
    Args:
        runes: 룬 리스트
        target: "A" (격노+칼날) 또는 "B" (맹공+칼날)
        gem_mode: "none" (현재 미구현)
        grind_mode: "none" (현재 미구현)
        top_n: 상위 N개 반환
        base_atk: 기본 공격력
        max_candidates_per_slot: fast 모드에서 슬롯당 최대 후보 수
        mode: "exhaustive" (모든 조합 탐색, 기본값) 또는 "fast" (heuristic pruning 사용)
    
    Returns:
        최적 조합 리스트
    """
    # 슬롯별 룬 분리
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = filter_rune_by_slot(runes, slot, target)
        if not slot_runes[slot]:
            return []  # 필수 슬롯에 룬이 없으면 빈 결과
    
    results = []
    rune_dict = {r.rune_id: r for r in runes}
    
    if mode == "exhaustive":
        # Exhaustive 모드: DFS로 모든 조합 탐색
        def dfs_exhaustive(current_slot: int, state: DPState):
            if current_slot > 6:
                # 6개 슬롯 모두 선택 완료
                rune_combo = [rune_dict[rid] for rid in state.rune_ids if rid in rune_dict]
                if len(rune_combo) != 6:
                    return
                
                # 무형 배치 최적화
                assignment, score, stats = find_best_intangible_assignment(
                    rune_combo, target, base_atk, require_cr_100=True, require_sets=True
                )
                
                if score > 0:
                    results.append({
                        "runes": rune_combo,
                        "score": score,
                        "stats": stats,
                        "intangible_assignment": assignment,
                    })
                return
            
            # 현재 슬롯의 룬들을 시도
            for rune in slot_runes[current_slot]:
                new_state = state.add_rune(rune)
                dfs_exhaustive(current_slot + 1, new_state)
        
        initial_state = DPState()
        dfs_exhaustive(1, initial_state)
    
    else:
        # Fast 모드: DP with pruning
        dp = [{} for _ in range(7)]
        initial_state = DPState()
        dp[0][initial_state] = initial_state
        
        for slot in range(1, 7):
            current_dp = {}
            candidate_states = []
            
            for prev_state in dp[slot - 1].values():
                # 세트 요구사항 pruning
                if not check_set_requirements(prev_state, slot_runes, slot - 1, target, require_sets=True):
                    continue
                
                for rune in slot_runes[slot]:
                    new_state = prev_state.add_rune(rune)
                    
                    # 세트 요구사항 pruning
                    if not check_set_requirements(new_state, slot_runes, slot, target, require_sets=True):
                        continue
                    
                    # 상태 키로 그룹화하여 최선만 유지
                    state_key = (new_state.count_rage, new_state.count_fatal, 
                               new_state.count_blade, new_state.count_intangible)
                    
                    if state_key not in current_dp:
                        current_dp[state_key] = new_state
                        candidate_states.append(new_state)
                    else:
                        existing = current_dp[state_key]
                        existing_score = calculate_heuristic_score(existing, base_atk)
                        new_score = calculate_heuristic_score(new_state, base_atk)
                        
                        if new_score > existing_score:
                            current_dp[state_key] = new_state
                            if existing in candidate_states:
                                candidate_states.remove(existing)
                            candidate_states.append(new_state)
            
            # 상위 K개만 유지
            if len(candidate_states) > max_candidates_per_slot:
                candidate_states.sort(key=lambda s: calculate_heuristic_score(s, base_atk), reverse=True)
                candidate_states = candidate_states[:max_candidates_per_slot]
                current_dp = {s: current_dp.get((s.count_rage, s.count_fatal, s.count_blade, s.count_intangible), s) 
                             for s in candidate_states}
            
            dp[slot] = current_dp
        
        # 최종 상태에서 최적 조합 찾기
        for final_state in dp[6].values():
            rune_combo = [rune_dict[rid] for rid in final_state.rune_ids if rid in rune_dict]
            if len(rune_combo) != 6:
                continue
            
            assignment, score, stats = find_best_intangible_assignment(
                rune_combo, target, base_atk, require_cr_100=True, require_sets=True
            )
            
            if score > 0:
                results.append({
                    "runes": rune_combo,
                    "score": score,
                    "stats": stats,
                    "intangible_assignment": assignment,
                })
    
    # 스코어 기준 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 상위 N개만 반환
    top_results = results[:top_n]
    
    # 결과 포맷팅
    formatted_results = []
    for result in top_results:
        rune_combo = result["runes"]
        stats = result["stats"]
        
        # 슬롯별 룬 정보
        slot_info = {}
        for rune in rune_combo:
            prefix_str = ""
            if rune.has_prefix:
                prefix_str = f"{rune.prefix_stat_name} {rune.prefix_stat_value}"
            
            slot_info[rune.slot] = {
                "rune_id": rune.rune_id,
                "set_name": rune.set_name,
                "main": f"{rune.main_stat_name} {rune.main_stat_value}",
                "prefix": prefix_str,
                "subs": [f"{STAT_ID_NAME.get(sub.stat_id, '?')} {sub.value}" 
                        for sub in rune.subs]
            }
        
        formatted_results.append({
            "score": result["score"],
            "cr_total": stats["cr_total"],
            "cd_total": stats["cd_total"],
            "atk_pct_total": stats["atk_pct_total"],
            "atk_flat_total": stats["atk_flat_total"],
            "atk_bonus": stats["atk_bonus"],
            "atk_total": stats["atk_total"],
            "spd_total": stats["spd_total"],
            "intangible_assignment": result["intangible_assignment"],
            "slots": slot_info,
        })
    
    return formatted_results


def search_builds(runes: List[Rune], target: str = "B",
                  base_atk: int = 900, base_spd: int = 104,
                  constraints: Dict[str, float] = None,
                  objective: str = "SCORE",
                  top_n: int = 20,
                  return_policy: str = "top_n",
                  return_all: bool = False,
                  max_results: int = 2000,
                  max_candidates_per_slot: int = 300,
                  mode: str = "exhaustive",
                  require_sets: bool = True,
                  allow_any_main: bool = False) -> List[Dict]:
    """
    조건 기반 최적 조합 탐색 (SWOP 스타일)
    
    ⚠️ 중요: exhaustive 모드에서는 정확도 100% 보장 (heuristic pruning 없음)
    - exhaustive 모드: feasibility pruning과 upper-bound pruning만 사용
    - fast 모드: 정확도 보장 없음 (heuristic pruning 사용)
    
    Args:
        runes: 룬 리스트
        target: "A" (격노+칼날) 또는 "B" (맹공+칼날)
        base_atk: 기본 공격력
        base_spd: 기본 속도
        constraints: 최소 조건 딕셔너리 (예: {"SPD": 100, "CR": 100, "ATK_TOTAL": 2000, "MIN_SCORE": 4800})
        objective: 정렬 기준 ("SCORE", "ATK_TOTAL", "ATK_BONUS", "CD", "SPD")
        top_n: 상위 N개 반환 (return_all=False일 때만 적용)
        return_policy: "top_n" 또는 "all_at_best"
        return_all: True면 조건 만족하는 모든 빌드 반환 (메모리 주의)
        max_results: fast 모드에서만 사용되는 최대 결과 수 제한
        max_candidates_per_slot: fast 모드에서만 사용 (exhaustive 모드에서는 무시)
        mode: "exhaustive" (정확도 100% 보장) 또는 "fast" (정확도 보장 없음)
        require_sets: True면 target 세트 조건 필수, False면 모든 세트 허용
        allow_any_main: True면 slot 2/4/6 메인스탯 제한 해제
    
    Returns:
        조건을 만족하는 조합 리스트
    
    Examples:
        >>> # Exhaustive search with constraints (정확도 100%)
        >>> results = search_builds(runes, target="B", constraints={"CR": 100, "SPD": 100}, mode="exhaustive")
        
        >>> # Any set search (SWOP-like)
        >>> results = search_builds(runes, require_sets=False, constraints={"CR": 100}, mode="exhaustive")
        
        >>> # Return all matching builds
        >>> results = search_builds(runes, constraints={"CR": 100}, return_all=True, mode="exhaustive")
        
        >>> # Fast mode (정확도 보장 없음)
        >>> results = search_builds(runes, mode="fast", max_candidates_per_slot=100)
    """
    if constraints is None:
        constraints = {}
    
    # CR>=100 hardcode 제거: constraints에 CR이 있으면 require_cr_100=False
    require_cr_100 = "CR" not in constraints
    
    # exhaustive 모드에서는 max_candidates_per_slot 사용 금지
    if mode == "exhaustive" and max_candidates_per_slot < float('inf'):
        # exhaustive 모드에서는 후보 제한 없음
        pass
    
    # 슬롯별 룬 분리
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = filter_rune_by_slot(runes, slot, target, allow_any_main=allow_any_main)
        if not slot_runes[slot]:
            return []
    
    # exhaustive 모드: fast 모드에서만 후보 제한 적용
    if mode == "fast":
        # 슬롯별 후보 수가 많으면 상위 K개만 유지 (heuristic pruning)
        for slot in range(1, 7):
            if len(slot_runes[slot]) > max_candidates_per_slot:
                # 휴리스틱 스코어로 정렬하여 상위 K개만 유지
                slot_runes[slot].sort(key=lambda r: calculate_heuristic_score(DPState().add_rune(r), base_atk), reverse=True)
                slot_runes[slot] = slot_runes[slot][:max_candidates_per_slot]
    
    # 슬롯 탐색 순서 최적화: 후보 수가 적은 슬롯부터 (정확도 영향 없음)
    slot_order = sorted(range(1, 7), key=lambda s: len(slot_runes[s]))
    
    # DFS로 모든 조합 탐색
    results = []
    rune_dict = {r.rune_id: r for r in runes}
    
    # Upper-bound pruning을 위한 최저 점수 추적 (top_n 모드일 때만)
    
    def calculate_upper_bound(state: DPState, current_slot: int) -> float:
        """남은 슬롯에서 얻을 수 있는 최대 점수 상한 계산 (upper-bound pruning용)"""
        if current_slot > 6:
            return 0.0
        
        max_remaining = calculate_max_remaining_stats(slot_runes, current_slot + 1)
        max_remaining_sets = calculate_max_remaining_sets(slot_runes, current_slot + 1)
        
        # 현재까지의 스탯
        current_cd = BASE_CD + state.cd
        current_atk_pct = state.atk_pct
        current_atk_flat = state.atk_flat
        
        # 세트 보너스 고려 (최선의 경우)
        if target == "A":
            potential_rage = state.count_rage + max_remaining_sets["RAGE"] + (state.count_intangible if state.count_intangible > 0 else 0)
            if potential_rage >= 4:
                current_cd += 40
        else:  # target == "B"
            potential_fatal = state.count_fatal + max_remaining_sets["FATAL"] + (state.count_intangible if state.count_intangible > 0 else 0)
            if potential_fatal >= 4:
                max_remaining["ATK_PCT"] += 35
        
        # 최대 예상 스탯
        max_cd = current_cd + max_remaining["CD"]
        max_atk_pct = current_atk_pct + max_remaining["ATK_PCT"]
        max_atk_flat = current_atk_flat + max_remaining["ATK_FLAT"]
        
        # 최대 예상 점수
        max_atk_bonus = round(base_atk * (max_atk_pct / 100.0) + max_atk_flat)
        max_score = (max_cd * 10) + max_atk_bonus + 200
        
        return max_score
    
    def dfs(current_slot_idx: int, state: DPState):
        """DFS로 조합 탐색"""
        current_slot = slot_order[current_slot_idx] if current_slot_idx < len(slot_order) else 7
        
        # fast 모드에서만 early stop
        if mode == "fast" and len(results) >= max_results:
            return
        
        # Upper-bound pruning (top_n 모드일 때만, exhaustive 모드에서도 사용)
        if not return_all and top_n > 0 and len(results) >= top_n:
            upper_bound = calculate_upper_bound(state, current_slot)
            # 현재 결과의 최저 점수보다 상한이 낮으면 가지치기
            if len(results) >= top_n:
                # 결과를 objective 기준으로 정렬하여 최저값 확인
                if objective == "SCORE":
                    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
                    min_score = sorted_results[top_n - 1]["score"]
                elif objective == "ATK_TOTAL":
                    sorted_results = sorted(results, key=lambda x: x["stats"]["atk_total"], reverse=True)
                    min_score = sorted_results[top_n - 1]["stats"]["atk_total"]
                elif objective == "ATK_BONUS":
                    sorted_results = sorted(results, key=lambda x: x["stats"]["atk_bonus"], reverse=True)
                    min_score = sorted_results[top_n - 1]["stats"]["atk_bonus"]
                elif objective == "CD":
                    sorted_results = sorted(results, key=lambda x: x["stats"]["cd_total"], reverse=True)
                    min_score = sorted_results[top_n - 1]["stats"]["cd_total"]
                elif objective == "SPD":
                    sorted_results = sorted(results, key=lambda x: x["stats"]["spd_total"], reverse=True)
                    min_score = sorted_results[top_n - 1]["stats"]["spd_total"]
                else:
                    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
                    min_score = sorted_results[top_n - 1]["score"]
                
                # upper_bound는 SCORE 기준이므로 objective가 SCORE일 때만 비교
                if objective == "SCORE" and upper_bound < min_score:
                    return
        
        # Feasibility pruning: 세트 요구사항 체크 (exhaustive 모드에서도 사용)
        if not check_set_requirements(state, slot_runes, current_slot - 1, target, require_sets):
            return
        
        # Feasibility pruning: 제약 조건을 만족할 수 없으면 가지치기 (exhaustive 모드에서도 사용)
        if not check_constraints(state, constraints, slot_runes, current_slot - 1, base_atk, base_spd, target, require_sets):
            return
        
        if current_slot > 6:
            # 6개 슬롯 모두 선택 완료
            rune_combo = [rune_dict[rid] for rid in state.rune_ids if rid in rune_dict]
            if len(rune_combo) != 6:
                return
            
            # 무형 배치 최적화
            assignment, score, stats = find_best_intangible_assignment(
                rune_combo, target, base_atk, require_cr_100=require_cr_100, require_sets=require_sets
            )
            
            if score <= 0:
                return
            
            # 제약 조건 최종 확인
            if "CR" in constraints and stats["cr_total"] < constraints["CR"]:
                return
            if "CD" in constraints and stats["cd_total"] < constraints["CD"]:
                return
            if "SPD" in constraints and (base_spd + stats["spd_total"]) < constraints["SPD"]:
                return
            if "ATK_BONUS" in constraints and stats["atk_bonus"] < constraints["ATK_BONUS"]:
                return
            if "ATK_TOTAL" in constraints and stats["atk_total"] < constraints["ATK_TOTAL"]:
                return
            if "ATK_PCT" in constraints and stats["atk_pct_total"] < constraints["ATK_PCT"]:
                return
            if "ATK_FLAT" in constraints and stats["atk_flat_total"] < constraints["ATK_FLAT"]:
                return
            if "MIN_SCORE" in constraints and score < constraints["MIN_SCORE"]:
                return
            
            # score > 0이고 constraints를 만족하면 유효한 빌드
            results.append({
                "runes": rune_combo,
                "score": score,
                "stats": stats,
                "intangible_assignment": assignment,
            })
            return
        
        # 현재 슬롯의 룬들을 시도
        for rune in slot_runes[current_slot]:
            new_state = state.add_rune(rune)
            dfs(current_slot_idx + 1, new_state)
    
    # DFS 시작
    initial_state = DPState()
    dfs(0, initial_state)
    
    # 정렬
    if objective == "SCORE":
        results.sort(key=lambda x: x["score"], reverse=True)
    elif objective == "ATK_TOTAL":
        results.sort(key=lambda x: x["stats"]["atk_total"], reverse=True)
    elif objective == "ATK_BONUS":
        results.sort(key=lambda x: x["stats"]["atk_bonus"], reverse=True)
    elif objective == "CD":
        results.sort(key=lambda x: x["stats"]["cd_total"], reverse=True)
    elif objective == "SPD":
        results.sort(key=lambda x: x["stats"]["spd_total"], reverse=True)
    else:
        results.sort(key=lambda x: x["score"], reverse=True)
    
    # 반환 정책 적용
    if return_all:
        # return_all=True면 모든 결과 반환 (top_n 무시)
        pass
    elif return_policy == "all_at_best" and results:
        best_value = results[0]["score"] if objective == "SCORE" else results[0]["stats"].get(objective.lower(), 0)
        filtered = [r for r in results if (r["score"] if objective == "SCORE" else r["stats"].get(objective.lower(), 0)) == best_value]
        results = filtered[:top_n] if top_n > 0 else filtered
    else:
        results = results[:top_n] if top_n > 0 else results
    
    # 결과 포맷팅
    formatted_results = []
    for result in results:
        rune_combo = result["runes"]
        stats = result["stats"]
        
        # 슬롯별 룬 정보
        slot_info = {}
        for rune in rune_combo:
            prefix_str = ""
            if rune.has_prefix:
                prefix_str = f"{rune.prefix_stat_name} {rune.prefix_stat_value}"
            
            slot_info[rune.slot] = {
                "rune_id": rune.rune_id,
                "set_name": rune.set_name,
                "main": f"{rune.main_stat_name} {rune.main_stat_value}",
                "prefix": prefix_str,
                "subs": [f"{STAT_ID_NAME.get(sub.stat_id, '?')} {sub.value}" 
                        for sub in rune.subs]
            }
        
        formatted_results.append({
            "score": result["score"],
            "cr_total": stats["cr_total"],
            "cd_total": stats["cd_total"],
            "atk_pct_total": stats["atk_pct_total"],
            "atk_flat_total": stats["atk_flat_total"],
            "atk_bonus": stats["atk_bonus"],
            "atk_total": stats["atk_total"],
            "spd_total": stats["spd_total"],
            "intangible_assignment": result["intangible_assignment"],
            "slots": slot_info,
        })
    
    return formatted_results
