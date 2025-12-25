"""타입 정의 및 상수"""

from dataclasses import dataclass
from typing import List, Optional

# 세트 ID 매핑
SET_ID_NAME = {
    1: "Energy",
    2: "Guard",
    3: "Swift",
    4: "Blade",
    5: "Rage",
    6: "Focus",
    7: "Endure",
    8: "Fatal",
    10: "Despair",
    11: "Vampire",
    13: "Violent",
    14: "Nemesis",
    15: "Will",
    16: "Shield",
    17: "Revenge",
    18: "Destroy",
    19: "Fight",
    20: "Determination",
    21: "Enhance",
    22: "Accuracy",
    23: "Tolerance",
    25: "Intangible",  # 무형 세트 (실제 JSON에서 set_id=25)
    99: "Unknown",  # 기존 99는 Unknown으로 처리
}

# 스탯 ID 매핑
STAT_ID_NAME = {
    1: "HP",
    2: "HP%",
    3: "ATK",
    4: "ATK%",
    5: "DEF",
    6: "DEF%",
    8: "SPD",
    9: "CR",
    10: "CD",
    11: "RES",
    12: "ACC",
}

# 기본 스탯
BASE_CR = 15  # 기본 치명타 확률
BASE_CD = 50  # 기본 치명타 데미지

# 세트 보너스
RAGE_4SET_CD = 40  # Rage 4세트: CD +40
FATAL_4SET_ATK_PCT = 35  # Fatal 4세트: ATK% +35
BLADE_2SET_CR = 12  # Blade 2세트: CR +12


@dataclass
class SubStat:
    """서브 스탯"""
    stat_id: int
    value: float  # base + grind 최종 값
    enchanted: bool = False
    grind: float = 0.0


@dataclass
class Rune:
    """룬 정보"""
    rune_id: int
    slot: int
    set_id: int
    main_stat_id: int
    main_stat_value: float
    subs: List[SubStat]
    level: int = 0
    quality: int = 0
    prefix_stat_id: int = 0  # prefix_eff의 stat_id (0이면 없음)
    prefix_stat_value: float = 0.0  # prefix_eff의 value
    
    @property
    def set_name(self) -> str:
        return SET_ID_NAME.get(self.set_id, "Unknown")
    
    @property
    def intangible(self) -> bool:
        """무형 세트 여부 (set_id=25)"""
        return self.set_id == 25
    
    @property
    def main_stat_name(self) -> str:
        return STAT_ID_NAME.get(self.main_stat_id, "Unknown")
    
    @property
    def prefix_stat_name(self) -> str:
        if self.prefix_stat_id == 0:
            return ""
        return STAT_ID_NAME.get(self.prefix_stat_id, "Unknown")
    
    @property
    def has_prefix(self) -> bool:
        """prefix_eff가 있는지"""
        return self.prefix_stat_id != 0
    
    def get_sub_stat(self, stat_id: int) -> Optional[SubStat]:
        """특정 서브 스탯 반환"""
        for sub in self.subs:
            if sub.stat_id == stat_id:
                return sub
        return None
    
    def has_sub_stat(self, stat_id: int) -> bool:
        """특정 서브 스탯 존재 여부"""
        return self.get_sub_stat(stat_id) is not None

