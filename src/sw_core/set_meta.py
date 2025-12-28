"""룬 세트 메타데이터 - 2-set vs 4-set 정보"""

from typing import List, Tuple, Set

# 세트 완성에 필요한 룬 개수
SET_META = {
    "Energy": 2,
    "Guard": 2,
    "Swift": 4,
    "Blade": 2,
    "Rage": 4,
    "Focus": 2,
    "Endure": 2,
    "Fatal": 4,
    "Despair": 4,
    "Vampire": 4,
    "Violent": 4,
    "Nemesis": 2,
    "Will": 2,
    "Shield": 2,
    "Revenge": 2,
    "Destroy": 4,
    "Fight": 2,
    "Determination": 2,
    "Enhance": 2,
    "Accuracy": 2,
    "Tolerance": 2,
}

def get_set_requirement(set_name: str) -> int:
    """세트 완성에 필요한 룬 개수 반환 (2 또는 4)"""
    return SET_META.get(set_name, 2)  # 기본값 2-set

def is_4set(set_name: str) -> bool:
    """4-set인지 확인"""
    return get_set_requirement(set_name) == 4

def is_2set(set_name: str) -> bool:
    """2-set인지 확인"""
    return get_set_requirement(set_name) == 2


def generate_set_combinations(set_groups: List[List[str]]) -> List[Tuple[str, ...]]:
    """
    세트 그룹에서 가능한 조합 생성
    
    Args:
        set_groups: 각 그룹의 세트 리스트 (예: [["Rage", "Violent"], ["Blade"]])
    
    Returns:
        유효한 조합 튜플 리스트 (예: [("Rage", "Blade"), ("Violent", "Blade")])
    """
    from itertools import product
    
    # 비어있지 않은 그룹만 필터링
    non_empty_groups = [group for group in set_groups if group]
    
    if not non_empty_groups:
        return []  # 모든 그룹이 비어있으면 조합 없음
    
    # 모든 그룹에서 1개씩 선택한 데카르트 곱 생성
    all_combinations = list(product(*non_empty_groups))
    
    # 유효성 검증
    valid_combinations = []
    for combo in all_combinations:
        if is_valid_combination(combo):
            valid_combinations.append(combo)
    
    return valid_combinations


def is_valid_combination(combo: Tuple[str, ...]) -> bool:
    """
    조합이 유효한지 검증
    
    규칙:
    - required_count <= 6
    - 4-set 타입 세트가 2개 이상이면 무효 (4+4 불가)
    - 중복 세트는 허용 (하나로 합쳐서 계산)
    """
    # 중복 제거하여 고유 세트만 계산
    unique_sets = list(set(combo))
    
    # 필요한 룬 개수 합계
    required_count = sum(get_set_requirement(s) for s in unique_sets)
    
    # 6개 초과면 무효
    if required_count > 6:
        return False
    
    # 4-set 개수 확인
    fourset_count = sum(1 for s in unique_sets if is_4set(s))
    
    # 4-set이 2개 이상이면 무효 (4+4 불가)
    if fourset_count >= 2:
        return False
    
    return True


def get_required_count(combo: Tuple[str, ...]) -> int:
    """조합에 필요한 총 룬 개수"""
    unique_sets = list(set(combo))
    return sum(get_set_requirement(s) for s in unique_sets)


def get_allowed_sets(combo: Tuple[str, ...], strict: bool = True) -> Set[str]:
    """
    조합에서 허용되는 세트 집합 반환
    
    Args:
        combo: 세트 조합 튜플
        strict: True면 조합의 세트만 허용, False면 모든 세트 허용
    
    Returns:
        허용되는 세트 이름 집합
    """
    if strict:
        return set(combo)
    else:
        # 모든 세트 허용 (None 반환은 "제한 없음" 의미)
        return None  # 실제로는 모든 세트를 의미

