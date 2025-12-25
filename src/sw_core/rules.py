"""룬 빌드 규칙 (Single Source of Truth)"""

from typing import List, Optional
from .types import Rune, STAT_ID_NAME

# 게임 룰: 슬롯별 메인스탯 제약 (하드 제약)
# Slot 2: 메인에서 CD/CR/RES/ACC 선택 불가
SLOT_2_FORBIDDEN_MAIN = {10, 9, 11, 12}  # CD, CR, RES, ACC

# Slot 4: 메인에서 SPD/ACC/RES 선택 불가
SLOT_4_FORBIDDEN_MAIN = {8, 12, 11}  # SPD, ACC, RES

# Slot 6: 메인에서 SPD/CD/CR 선택 불가
SLOT_6_FORBIDDEN_MAIN = {8, 10, 9}  # SPD, CD, CR

# 추가 사용자 룰: 공격력/방어력 옵션 금지
FORBIDDEN_ATK_STATS = {3, 4}  # ATK, ATK%
FORBIDDEN_DEF_STATS = {5, 6}  # DEF, DEF%


def slot_main_is_allowed(slot: int, main_stat_id: int) -> bool:
    """
    슬롯에서 메인스탯이 허용되는지 확인
    
    Args:
        slot: 슬롯 번호 (1-6)
        main_stat_id: 메인 스탯 ID
    
    Returns:
        허용되면 True, 금지되면 False
    """
    if slot == 2:
        return main_stat_id not in SLOT_2_FORBIDDEN_MAIN
    elif slot == 4:
        return main_stat_id not in SLOT_4_FORBIDDEN_MAIN
    elif slot == 6:
        return main_stat_id not in SLOT_6_FORBIDDEN_MAIN
    else:
        # Slot 1, 3, 5는 메인스탯 제한 없음
        return True


def slot_sub_is_allowed(slot: int, main_stat_id: int, sub_stat_id: int) -> bool:
    """
    슬롯에서 서브스탯이 허용되는지 확인
    
    Args:
        slot: 슬롯 번호 (1-6)
        main_stat_id: 메인 스탯 ID (중복 금지 체크용)
        sub_stat_id: 서브 스탯 ID
    
    Returns:
        허용되면 True, 금지되면 False
    """
    # 규칙 1: 서브스탯은 메인스탯과 중복 불가
    if sub_stat_id == main_stat_id:
        return False
    
    # 규칙 2: Slot 3에서 공격력 옵션 금지 (ATK+, ATK%)
    if slot == 3 and sub_stat_id in FORBIDDEN_ATK_STATS:
        return False
    
    # 규칙 3: Slot 1에서 방어력 옵션 금지 (DEF+, DEF%)
    if slot == 1 and sub_stat_id in FORBIDDEN_DEF_STATS:
        return False
    
    return True


def slot_prefix_is_allowed(slot: int, prefix_stat_id: int) -> bool:
    """
    슬롯에서 접두옵(prefix)이 허용되는지 확인
    
    Args:
        slot: 슬롯 번호 (1-6)
        prefix_stat_id: 접두 스탯 ID
    
    Returns:
        허용되면 True, 금지되면 False
    """
    # 규칙 1: Slot 3에서 공격력 옵션 금지 (ATK+, ATK%)
    if slot == 3 and prefix_stat_id in FORBIDDEN_ATK_STATS:
        return False
    
    # 규칙 2: Slot 1에서 방어력 옵션 금지 (DEF+, DEF%)
    if slot == 1 and prefix_stat_id in FORBIDDEN_DEF_STATS:
        return False
    
    return True


def validate_rune(rune: Rune) -> bool:
    """
    룬 1개가 모든 규칙에 맞는지 검증
    
    Args:
        rune: 검증할 룬
    
    Returns:
        규칙에 맞으면 True, 위반하면 False
    """
    # 규칙 1: 메인스탯 제약 확인
    if not slot_main_is_allowed(rune.slot, rune.main_stat_id):
        return False
    
    # 규칙 2: 서브스탯 제약 확인 (메인 중복 + slot 1/3 제약)
    for sub in rune.subs:
        if not slot_sub_is_allowed(rune.slot, rune.main_stat_id, sub.stat_id):
            return False
    
    # 규칙 3: 접두옵(prefix) 제약 확인
    if rune.has_prefix:
        if not slot_prefix_is_allowed(rune.slot, rune.prefix_stat_id):
            return False
        # 접두옵도 메인스탯과 중복 불가
        if rune.prefix_stat_id == rune.main_stat_id:
            return False
    
    return True


def validate_build(runes: List[Rune]) -> bool:
    """
    6개 룬 조합이 모든 규칙에 맞는지 검증
    
    Args:
        runes: 6개 룬 리스트
    
    Returns:
        규칙에 맞으면 True, 위반하면 False
    """
    if len(runes) != 6:
        return False
    
    # 각 룬이 규칙에 맞는지 확인
    for rune in runes:
        if not validate_rune(rune):
            return False
    
    # 슬롯 중복 확인
    slots = [rune.slot for rune in runes]
    if len(set(slots)) != 6:
        return False
    
    return True


def filter_valid_runes(runes: List[Rune]) -> List[Rune]:
    """
    룬 리스트에서 규칙에 맞는 룬만 필터링
    
    Args:
        runes: 전체 룬 리스트
    
    Returns:
        규칙에 맞는 룬 리스트
    """
    return [rune for rune in runes if validate_rune(rune)]

