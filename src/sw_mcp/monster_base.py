"""몬스터 기본 스탯 조회 API"""

from typing import Optional, Dict, Any
from .db.repo import MonsterRepository
from .db.models import MonsterBase


def get_base_stats(com2us_id: int, db_url: str = None) -> Optional[Dict[str, Any]]:
    """
    com2us_id로 몬스터 기본 스탯 조회
    
    Args:
        com2us_id: SWEX unit_master_id (com2us_id)
        db_url: DB URL (None이면 환경변수/기본값 사용)
    
    Returns:
        기본 스탯 딕셔너리 또는 None (없으면)
        
    Example:
        >>> stats = get_base_stats(14105)  # 루쉔
        >>> if stats:
        ...     print(f"ATK: {stats['base_attack']}, SPD: {stats['speed']}")
    """
    repo = MonsterRepository()
    try:
        monster = repo.get_by_com2us_id(com2us_id)
        if monster:
            return monster.to_dict()
        return None
    finally:
        repo.close()


def get_base_stats_safe(com2us_id: int, fallback: Dict[str, Any] = None, db_url: str = None) -> Dict[str, Any]:
    """
    com2us_id로 몬스터 기본 스탯 조회 (fallback 지원)
    
    Args:
        com2us_id: SWEX unit_master_id
        fallback: DB에 없을 때 반환할 기본값
        db_url: DB URL
    
    Returns:
        기본 스탯 딕셔너리 (fallback 포함)
    
    Example:
        >>> stats = get_base_stats_safe(
        ...     14105,
        ...     fallback={"base_attack": 900, "base_defense": 500, "speed": 104}
        ... )
    """
    stats = get_base_stats(com2us_id, db_url)
    if stats:
        return stats
    
    # Fallback
    if fallback:
        return fallback
    
    # 기본 fallback
    return {
        "base_attack": 900,
        "base_defense": 500,
        "base_hp": 10000,
        "speed": 104,
        "crit_rate": 15.0,
        "crit_damage": 50.0,
        "resistance": 0.0,
        "accuracy": 0.0,
    }

