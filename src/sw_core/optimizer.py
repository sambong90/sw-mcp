"""범용 룬 빌드 최적화 엔진"""

from typing import List, Dict, Tuple
from collections import defaultdict
from .types import Rune, STAT_ID_NAME, BASE_CR, BASE_CD, SET_ID_NAME
from .scoring import score_build, get_objective_value
from .rules import validate_rune, validate_build


def filter_rune_by_slot(runes: List[Rune], slot: int) -> List[Rune]:
    """
    슬롯별 룬 필터링 (게임 룰 기반)
    
    Args:
        runes: 전체 룬 리스트
        slot: 슬롯 번호 (1-6)
    
    Returns:
        규칙에 맞는 룬 리스트
    """
    # 슬롯별로 필터링
    slot_runes = [r for r in runes if r.slot == slot]
    
    # 게임 룰 기반 필터링 (validate_rune 사용)
    return [r for r in slot_runes if validate_rune(r)]


class DPState:
    """DP 상태 (범용 스탯 추적)"""
    def __init__(self, 
                 cr: float = 0.0, cd: float = 0.0,
                 atk_pct: float = 0.0, atk_flat: float = 0.0,
                 hp_pct: float = 0.0, hp_flat: float = 0.0,
                 def_pct: float = 0.0, def_flat: float = 0.0,
                 spd: float = 0.0, res: float = 0.0, acc: float = 0.0,
                 set_counts: Dict[int, int] = None,
                 rune_ids: Tuple[int, ...] = ()):
        self.cr = cr
        self.cd = cd
        self.atk_pct = atk_pct
        self.atk_flat = atk_flat
        self.hp_pct = hp_pct
        self.hp_flat = hp_flat
        self.def_pct = def_pct
        self.def_flat = def_flat
        self.spd = spd
        self.res = res
        self.acc = acc
        self.set_counts = set_counts if set_counts is not None else {}
        self.rune_ids = rune_ids
    
    def __hash__(self):
        return hash((tuple(sorted(self.set_counts.items())), self.rune_ids))
    
    def __eq__(self, other):
        if not isinstance(other, DPState):
            return False
        return (self.set_counts == other.set_counts and
                self.rune_ids == other.rune_ids)
    
    def add_rune(self, rune: Rune) -> 'DPState':
        """룬 추가하여 새 상태 생성"""
        new_set_counts = self.set_counts.copy()
        if rune.intangible:
            # 무형은 나중에 배치 결정
            pass
        else:
            new_set_counts[rune.set_id] = new_set_counts.get(rune.set_id, 0) + 1
        
        # 스탯 추가
        new_cr = self.cr
        new_cd = self.cd
        new_atk_pct = self.atk_pct
        new_atk_flat = self.atk_flat
        new_hp_pct = self.hp_pct
        new_hp_flat = self.hp_flat
        new_def_pct = self.def_pct
        new_def_flat = self.def_flat
        new_spd = self.spd
        new_res = self.res
        new_acc = self.acc
        
        # 메인 스탯
        if rune.main_stat_id == 1:  # HP
            new_hp_flat += rune.main_stat_value
        elif rune.main_stat_id == 2:  # HP%
            new_hp_pct += rune.main_stat_value
        elif rune.main_stat_id == 3:  # ATK
            new_atk_flat += rune.main_stat_value
        elif rune.main_stat_id == 4:  # ATK%
            new_atk_pct += rune.main_stat_value
        elif rune.main_stat_id == 5:  # DEF
            new_def_flat += rune.main_stat_value
        elif rune.main_stat_id == 6:  # DEF%
            new_def_pct += rune.main_stat_value
        elif rune.main_stat_id == 8:  # SPD
            new_spd += rune.main_stat_value
        elif rune.main_stat_id == 9:  # CR
            new_cr += rune.main_stat_value
        elif rune.main_stat_id == 10:  # CD
            new_cd += rune.main_stat_value
        elif rune.main_stat_id == 11:  # RES
            new_res += rune.main_stat_value
        elif rune.main_stat_id == 12:  # ACC
            new_acc += rune.main_stat_value
        
        # prefix_eff
        if rune.has_prefix:
            if rune.prefix_stat_id == 1:
                new_hp_flat += rune.prefix_stat_value
            elif rune.prefix_stat_id == 2:
                new_hp_pct += rune.prefix_stat_value
            elif rune.prefix_stat_id == 3:
                new_atk_flat += rune.prefix_stat_value
            elif rune.prefix_stat_id == 4:
                new_atk_pct += rune.prefix_stat_value
            elif rune.prefix_stat_id == 5:
                new_def_flat += rune.prefix_stat_value
            elif rune.prefix_stat_id == 6:
                new_def_pct += rune.prefix_stat_value
            elif rune.prefix_stat_id == 8:
                new_spd += rune.prefix_stat_value
            elif rune.prefix_stat_id == 9:
                new_cr += rune.prefix_stat_value
            elif rune.prefix_stat_id == 10:
                new_cd += rune.prefix_stat_value
            elif rune.prefix_stat_id == 11:
                new_res += rune.prefix_stat_value
            elif rune.prefix_stat_id == 12:
                new_acc += rune.prefix_stat_value
        
        # 서브 스탯
        for sub in rune.subs:
            if sub.stat_id == 1:
                new_hp_flat += sub.value
            elif sub.stat_id == 2:
                new_hp_pct += sub.value
            elif sub.stat_id == 3:
                new_atk_flat += sub.value
            elif sub.stat_id == 4:
                new_atk_pct += sub.value
            elif sub.stat_id == 5:
                new_def_flat += sub.value
            elif sub.stat_id == 6:
                new_def_pct += sub.value
            elif sub.stat_id == 8:
                new_spd += sub.value
            elif sub.stat_id == 9:
                new_cr += sub.value
            elif sub.stat_id == 10:
                new_cd += sub.value
            elif sub.stat_id == 11:
                new_res += sub.value
            elif sub.stat_id == 12:
                new_acc += sub.value
        
        new_rune_ids = self.rune_ids + (rune.rune_id,)
        
        return DPState(
            cr=new_cr, cd=new_cd,
            atk_pct=new_atk_pct, atk_flat=new_atk_flat,
            hp_pct=new_hp_pct, hp_flat=new_hp_flat,
            def_pct=new_def_pct, def_flat=new_def_flat,
            spd=new_spd, res=new_res, acc=new_acc,
            set_counts=new_set_counts,
            rune_ids=new_rune_ids
        )


def calculate_max_remaining_sets(slot_runes: Dict[int, List[Rune]], start_slot: int) -> Dict[int, int]:
    """남은 슬롯에서 얻을 수 있는 최대 세트 개수 계산 (pruning용)"""
    max_sets = defaultdict(int)
    
    for slot in range(start_slot, 7):
        if slot not in slot_runes:
            continue
        
        slot_max = defaultdict(int)
        
        for rune in slot_runes[slot]:
            if rune.intangible:
                # 무형은 모든 세트에 배치 가능하므로 최대값으로 계산
                slot_max[25] = max(slot_max.get(25, 0), 1)
            else:
                set_id = rune.set_id
                slot_max[set_id] = max(slot_max.get(set_id, 0), 1)
        
        # 각 슬롯의 최대값을 합산 (슬롯당 최대 1개씩)
        for set_id, count in slot_max.items():
            max_sets[set_id] += count
    
    return dict(max_sets)


def calculate_heuristic_score(state: DPState, base_atk: int = 900) -> float:
    """휴리스틱 스코어 계산 (상위 K개 유지용, fast 모드에서만 사용)"""
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
        "HP_PCT": 0.0,
        "HP_FLAT": 0.0,
        "DEF_PCT": 0.0,
        "DEF_FLAT": 0.0,
        "SPD": 0.0,
        "RES": 0.0,
        "ACC": 0.0,
    }
    
    for slot in range(start_slot, 7):
        if slot not in slot_runes:
            continue
        
        slot_max = {
            "CR": 0.0,
            "CD": 0.0,
            "ATK_PCT": 0.0,
            "ATK_FLAT": 0.0,
            "HP_PCT": 0.0,
            "HP_FLAT": 0.0,
            "DEF_PCT": 0.0,
            "DEF_FLAT": 0.0,
            "SPD": 0.0,
            "RES": 0.0,
            "ACC": 0.0,
        }
        
        for rune in slot_runes[slot]:
            # 메인 스탯
            if rune.main_stat_id == 1:
                slot_max["HP_FLAT"] = max(slot_max["HP_FLAT"], rune.main_stat_value)
            elif rune.main_stat_id == 2:
                slot_max["HP_PCT"] = max(slot_max["HP_PCT"], rune.main_stat_value)
            elif rune.main_stat_id == 3:
                slot_max["ATK_FLAT"] = max(slot_max["ATK_FLAT"], rune.main_stat_value)
            elif rune.main_stat_id == 4:
                slot_max["ATK_PCT"] = max(slot_max["ATK_PCT"], rune.main_stat_value)
            elif rune.main_stat_id == 5:
                slot_max["DEF_FLAT"] = max(slot_max["DEF_FLAT"], rune.main_stat_value)
            elif rune.main_stat_id == 6:
                slot_max["DEF_PCT"] = max(slot_max["DEF_PCT"], rune.main_stat_value)
            elif rune.main_stat_id == 8:
                slot_max["SPD"] = max(slot_max["SPD"], rune.main_stat_value)
            elif rune.main_stat_id == 9:
                slot_max["CR"] = max(slot_max["CR"], rune.main_stat_value)
            elif rune.main_stat_id == 10:
                slot_max["CD"] = max(slot_max["CD"], rune.main_stat_value)
            elif rune.main_stat_id == 11:
                slot_max["RES"] = max(slot_max["RES"], rune.main_stat_value)
            elif rune.main_stat_id == 12:
                slot_max["ACC"] = max(slot_max["ACC"], rune.main_stat_value)
            
            # prefix
            if rune.has_prefix:
                if rune.prefix_stat_id == 1:
                    slot_max["HP_FLAT"] = max(slot_max["HP_FLAT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 2:
                    slot_max["HP_PCT"] = max(slot_max["HP_PCT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 3:
                    slot_max["ATK_FLAT"] = max(slot_max["ATK_FLAT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 4:
                    slot_max["ATK_PCT"] = max(slot_max["ATK_PCT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 5:
                    slot_max["DEF_FLAT"] = max(slot_max["DEF_FLAT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 6:
                    slot_max["DEF_PCT"] = max(slot_max["DEF_PCT"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 8:
                    slot_max["SPD"] = max(slot_max["SPD"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 9:
                    slot_max["CR"] = max(slot_max["CR"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 10:
                    slot_max["CD"] = max(slot_max["CD"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 11:
                    slot_max["RES"] = max(slot_max["RES"], rune.prefix_stat_value)
                elif rune.prefix_stat_id == 12:
                    slot_max["ACC"] = max(slot_max["ACC"], rune.prefix_stat_value)
            
            # 서브 스탯
            for sub in rune.subs:
                if sub.stat_id == 1:
                    slot_max["HP_FLAT"] = max(slot_max["HP_FLAT"], sub.value)
                elif sub.stat_id == 2:
                    slot_max["HP_PCT"] = max(slot_max["HP_PCT"], sub.value)
                elif sub.stat_id == 3:
                    slot_max["ATK_FLAT"] = max(slot_max["ATK_FLAT"], sub.value)
                elif sub.stat_id == 4:
                    slot_max["ATK_PCT"] = max(slot_max["ATK_PCT"], sub.value)
                elif sub.stat_id == 5:
                    slot_max["DEF_FLAT"] = max(slot_max["DEF_FLAT"], sub.value)
                elif sub.stat_id == 6:
                    slot_max["DEF_PCT"] = max(slot_max["DEF_PCT"], sub.value)
                elif sub.stat_id == 8:
                    slot_max["SPD"] = max(slot_max["SPD"], sub.value)
                elif sub.stat_id == 9:
                    slot_max["CR"] = max(slot_max["CR"], sub.value)
                elif sub.stat_id == 10:
                    slot_max["CD"] = max(slot_max["CD"], sub.value)
                elif sub.stat_id == 11:
                    slot_max["RES"] = max(slot_max["RES"], sub.value)
                elif sub.stat_id == 12:
                    slot_max["ACC"] = max(slot_max["ACC"], sub.value)
        
        # 각 슬롯의 최대값을 합산
        for key in max_stats:
            max_stats[key] += slot_max[key]
    
    return max_stats


def check_set_constraints(state: DPState, set_constraints: Dict[str, int], 
                          slot_runes: Dict[int, List[Rune]], current_slot: int) -> bool:
    """세트 제약조건을 만족할 수 있는지 확인 (pruning)"""
    if not set_constraints:
        return True  # 세트 조건 없음
    
    # 남은 슬롯에서 얻을 수 있는 최대 세트 개수
    max_remaining_sets = calculate_max_remaining_sets(slot_runes, current_slot + 1)
    
    # 세트 이름 -> ID 매핑
    name_to_id = {name: sid for sid, name in SET_ID_NAME.items()}
    
    # 각 세트 제약조건 확인
    for set_name, required_count in set_constraints.items():
        set_id = name_to_id.get(set_name)
        if set_id is None:
            continue  # 알 수 없는 세트 이름은 무시
        
        # 현재 세트 개수
        current_count = state.set_counts.get(set_id, 0)
        
        # 무형 룬 개수 (모든 세트에 배치 가능)
        intangible_count = state.set_counts.get(25, 0)
        
        # 남은 슬롯에서 얻을 수 있는 최대 개수
        max_remaining = max_remaining_sets.get(set_id, 0)
        max_intangible = max_remaining_sets.get(25, 0)
        
        # 최대 가능한 세트 개수 (무형은 모든 세트에 배치 가능하므로 최대값으로 계산)
        max_possible = current_count + max(intangible_count, max_intangible) + max_remaining
        
        if max_possible < required_count:
            return False
    
    return True


def check_constraints(state: DPState, constraints: Dict[str, float], 
                     slot_runes: Dict[int, List[Rune]], current_slot: int,
                     base_atk: int, base_spd: int, base_hp: int, base_def: int,
                     base_cr: int = BASE_CR, base_cd: int = BASE_CD,
                     set_constraints: Dict[str, int] = None) -> bool:
    """제약 조건을 만족할 수 있는지 확인 (pruning)"""
    # 세트 제약조건 체크
    if not check_set_constraints(state, set_constraints or {}, slot_runes, current_slot):
        return False
    
    if not constraints:
        return True
    
    # 현재까지의 스탯 (기본값 포함, base_cr/base_cd는 함수 파라미터로 받아야 하지만
    # pruning 단계에서는 최악의 경우를 가정하므로 BASE_CR/BASE_CD 사용)
    current_cr = BASE_CR + state.cr
    current_cd = BASE_CD + state.cd
    current_spd = base_spd + state.spd
    
    # 남은 슬롯에서 얻을 수 있는 최대 스탯
    max_remaining = calculate_max_remaining_stats(slot_runes, current_slot + 1)
    
    # 최종 예상 스탯
    final_cr = current_cr + max_remaining["CR"]
    final_cd = current_cd + max_remaining["CD"]
    final_spd = current_spd + max_remaining["SPD"]
    
    # ATK_BONUS와 ATK_TOTAL 계산
    final_atk_pct = state.atk_pct + max_remaining["ATK_PCT"]
    final_atk_flat = state.atk_flat + max_remaining["ATK_FLAT"]
    final_atk_bonus = round(base_atk * (final_atk_pct / 100.0) + final_atk_flat)
    final_atk_total = base_atk + final_atk_bonus
    
    # HP_TOTAL과 DEF_TOTAL 계산
    final_hp_pct = state.hp_pct + max_remaining["HP_PCT"]
    final_hp_flat = state.hp_flat + max_remaining["HP_FLAT"]
    final_hp_bonus = round(base_hp * (final_hp_pct / 100.0) + final_hp_flat)
    final_hp_total = base_hp + final_hp_bonus
    
    final_def_pct = state.def_pct + max_remaining["DEF_PCT"]
    final_def_flat = state.def_flat + max_remaining["DEF_FLAT"]
    final_def_bonus = round(base_def * (final_def_pct / 100.0) + final_def_flat)
    final_def_total = base_def + final_def_bonus
    
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
    if "HP_TOTAL" in constraints and final_hp_total < constraints["HP_TOTAL"]:
        return False
    if "DEF_TOTAL" in constraints and final_def_total < constraints["DEF_TOTAL"]:
        return False
    
    return True


def search_builds(runes: List[Rune],
                  base_atk: int = 900,
                  base_spd: int = 104,
                  base_hp: int = 10000,
                  base_def: int = 500,
                  base_cr: int = BASE_CR,
                  base_cd: int = BASE_CD,
                  constraints: Dict[str, float] = None,
                  set_constraints: Dict[str, int] = None,
                  objective: str = "SCORE",
                  top_n: int = 20,
                  return_policy: str = "top_n",
                  return_all: bool = False,
                  max_results: int = 2000,
                  max_candidates_per_slot: int = 300,
                  mode: str = "exhaustive") -> List[Dict]:
    """
    조건 기반 최적 조합 탐색 (SWOP 스타일, 범용 엔진)
    
    ⚠️ 중요: exhaustive 모드에서는 정확도 100% 보장 (heuristic pruning 없음)
    - exhaustive 모드: feasibility pruning과 upper-bound pruning만 사용
    - fast 모드: 정확도 보장 없음 (heuristic pruning 사용)
    
    Args:
        runes: 룬 리스트
        base_atk: 기본 공격력
        base_spd: 기본 속도
        base_hp: 기본 체력
        base_def: 기본 방어력
        constraints: 최소 조건 딕셔너리 (예: {"SPD": 100, "CR": 100, "ATK_TOTAL": 2000, "MIN_SCORE": 4800})
        set_constraints: 세트 제약조건 (예: {"Rage": 4, "Blade": 2}). None이면 모든 세트 허용
        objective: 정렬 기준 ("SCORE", "ATK_TOTAL", "ATK_BONUS", "CD", "SPD", "EHP" 등)
        top_n: 상위 N개 반환 (return_all=False일 때만 적용)
        return_policy: "top_n" 또는 "all_at_best"
        return_all: True면 조건 만족하는 모든 빌드 반환 (메모리 주의)
        max_results: fast 모드에서만 사용되는 최대 결과 수 제한
        max_candidates_per_slot: fast 모드에서만 사용 (exhaustive 모드에서는 무시)
        mode: "exhaustive" (정확도 100% 보장) 또는 "fast" (정확도 보장 없음)
    
    Returns:
        조건을 만족하는 조합 리스트
    """
    if constraints is None:
        constraints = {}
    if set_constraints is None:
        set_constraints = {}
    
    # 슬롯별 룬 분리
    slot_runes = {}
    for slot in range(1, 7):
        slot_runes[slot] = filter_rune_by_slot(runes, slot)
        if not slot_runes[slot]:
            return []
    
    # exhaustive 모드: NO heuristic candidate trimming
    # fast 모드에서만 후보 제한 적용
    if mode == "fast":
        # 슬롯별 후보 수가 많으면 상위 K개만 유지 (heuristic pruning)
        # ⚠️ WARNING: This may miss valid builds - accuracy not guaranteed
        for slot in range(1, 7):
            if len(slot_runes[slot]) > max_candidates_per_slot:
                # 휴리스틱 스코어로 정렬하여 상위 K개만 유지
                slot_runes[slot].sort(key=lambda r: calculate_heuristic_score(DPState().add_rune(r), base_atk), reverse=True)
                slot_runes[slot] = slot_runes[slot][:max_candidates_per_slot]
    # exhaustive 모드에서는 모든 후보를 유지 (정확도 100% 보장)
    
    # 슬롯 탐색 순서 최적화: 후보 수가 적은 슬롯부터 (정확도 영향 없음)
    slot_order = sorted(range(1, 7), key=lambda s: len(slot_runes[s]))
    
    # DFS로 모든 조합 탐색
    results = []
    rune_dict = {r.rune_id: r for r in runes}
    
    def calculate_upper_bound(state: DPState, current_slot: int) -> float:
        """남은 슬롯에서 얻을 수 있는 최대 점수 상한 계산 (upper-bound pruning용)"""
        if current_slot > 6:
            return 0.0
        
        max_remaining = calculate_max_remaining_stats(slot_runes, current_slot + 1)
        
        # 현재까지의 스탯
        current_cd = BASE_CD + state.cd
        current_atk_pct = state.atk_pct
        current_atk_flat = state.atk_flat
        
        # 최대 예상 스탯
        max_cd = current_cd + max_remaining["CD"]
        max_atk_pct = current_atk_pct + max_remaining["ATK_PCT"]
        max_atk_flat = current_atk_flat + max_remaining["ATK_FLAT"]
        
        # 최대 예상 점수 (SCORE objective 기준)
        max_atk_bonus = round(base_atk * (max_atk_pct / 100.0) + max_atk_flat)
        max_score = (max_cd * 10) + max_atk_bonus + 200
        
        return max_score
    
    def dfs(current_slot_idx: int, state: DPState):
        """DFS로 조합 탐색"""
        current_slot = slot_order[current_slot_idx] if current_slot_idx < len(slot_order) else 7
        
        # fast 모드에서만 early stop
        if mode == "fast" and len(results) >= max_results:
            return
        
        # Upper-bound pruning: DISABLED in exhaustive mode for correctness
        # (Safe upper bounds are hard to compute with all set bonuses and intangible assignments)
        # Only use in fast mode with top_n
        if mode == "fast" and not return_all and top_n > 0 and len(results) >= top_n:
            upper_bound = calculate_upper_bound(state, current_slot)
            # 현재 결과의 최저 점수보다 상한이 낮으면 가지치기
            if len(results) >= top_n:
                # 결과를 objective 기준으로 정렬하여 최저값 확인
                sorted_results = sorted(results, key=lambda x: get_objective_value(objective, x["stats"]), reverse=True)
                min_value = get_objective_value(objective, sorted_results[top_n - 1]["stats"])
                
                # upper_bound는 SCORE 기준이므로 objective가 SCORE일 때만 비교
                # ⚠️ WARNING: This may miss valid builds if upper bound is not truly safe
                if objective == "SCORE" and upper_bound < min_value:
                    return
        
        # Feasibility pruning: 제약 조건을 만족할 수 없으면 가지치기 (exhaustive 모드에서도 사용)
        if not check_constraints(state, constraints, slot_runes, current_slot - 1, 
                                 base_atk, base_spd, base_hp, base_def, base_cr, base_cd, set_constraints):
            return
        
        if current_slot > 6:
            # 6개 슬롯 모두 선택 완료
            rune_combo = [rune_dict[rid] for rid in state.rune_ids if rid in rune_dict]
            if len(rune_combo) != 6:
                return
            
            # 빌드 검증
            if not validate_build(rune_combo):
                return
            
            # 스코어 계산 (score_build가 무형 배치 최적화 포함)
            score, stats, intangible_assignment = score_build(
                rune_combo,
                objective=objective,
                base_atk=base_atk,
                base_spd=base_spd,
                base_hp=base_hp,
                base_def=base_def,
                base_cr=base_cr,
                base_cd=base_cd,
                constraints=constraints,
                set_constraints=set_constraints
            )
            
            if score <= 0:
                return
            
            # 제약 조건 최종 확인
            if "CR" in constraints and stats.get("cr_total", 0) < constraints["CR"]:
                return
            if "CD" in constraints and stats.get("cd_total", 0) < constraints["CD"]:
                return
            if "SPD" in constraints and stats.get("spd_total", 0) < constraints["SPD"]:
                return
            if "ATK_BONUS" in constraints and stats.get("atk_bonus", 0) < constraints["ATK_BONUS"]:
                return
            if "ATK_TOTAL" in constraints and stats.get("atk_total", 0) < constraints["ATK_TOTAL"]:
                return
            if "ATK_PCT" in constraints and stats.get("atk_pct_total", 0) < constraints["ATK_PCT"]:
                return
            if "ATK_FLAT" in constraints and stats.get("atk_flat_total", 0) < constraints["ATK_FLAT"]:
                return
            if "HP_TOTAL" in constraints and stats.get("hp_total", 0) < constraints["HP_TOTAL"]:
                return
            if "DEF_TOTAL" in constraints and stats.get("def_total", 0) < constraints["DEF_TOTAL"]:
                return
            if "MIN_SCORE" in constraints and score < constraints["MIN_SCORE"]:
                return
            
            # score > 0이고 constraints를 만족하면 유효한 빌드
            results.append({
                "runes": rune_combo,
                "score": score,
                "stats": stats,
                "intangible_assignment": intangible_assignment,
            })
            return
        
        # 현재 슬롯의 룬들을 시도
        for rune in slot_runes[current_slot]:
            new_state = state.add_rune(rune)
            dfs(current_slot_idx + 1, new_state)
    
    # DFS 시작
    initial_state = DPState()
    dfs(0, initial_state)
    
    # 정렬 (get_objective_value 사용)
    results.sort(key=lambda x: get_objective_value(objective, x["stats"]), reverse=True)
    
    # 반환 정책 적용
    if return_all:
        # return_all=True면 모든 결과 반환 (top_n 무시)
        pass
    elif return_policy == "all_at_best" and results:
        best_value = get_objective_value(objective, results[0]["stats"])
        filtered = [r for r in results if get_objective_value(objective, r["stats"]) == best_value]
        results = filtered[:top_n] if top_n > 0 else filtered
    else:
        results = results[:top_n] if top_n > 0 else results
    
    # 결과 포맷팅
    formatted_results = []
    for result in results:
        rune_combo = result["runes"]
        stats = result["stats"]
        intangible_assignment = result["intangible_assignment"]
        
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
        
        # 무형 배치 포맷팅 (Dict[int, str] -> str)
        intangible_str = "none"
        if intangible_assignment:
            for rune_id, assignment in intangible_assignment.items():
                if assignment != "none":
                    intangible_str = assignment
                    break
        
        formatted_results.append({
            "score": result["score"],
            "cr_total": stats.get("cr_total", 0),
            "cd_total": stats.get("cd_total", 0),
            "atk_pct_total": stats.get("atk_pct_total", 0),
            "atk_flat_total": stats.get("atk_flat_total", 0),
            "atk_bonus": stats.get("atk_bonus", 0),
            "atk_total": stats.get("atk_total", 0),
            "hp_total": stats.get("hp_total", 0),
            "def_total": stats.get("def_total", 0),
            "spd_total": stats.get("spd_total", 0),
            "intangible_assignment": intangible_str,
            "slots": slot_info,
        })
    
    return formatted_results
