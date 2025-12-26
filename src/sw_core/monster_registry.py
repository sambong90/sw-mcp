"""몬스터 레지스트리 - 기본 스탯 자동 조회"""

import csv
import os
from typing import Optional, Dict, List
from pathlib import Path
from .types import MonsterBaseStats, BASE_CR, BASE_CD


class MonsterRegistry:
    """몬스터 기본 스탯 레지스트리
    
    조회 우선순위:
    1. DB (운영 기본)
    2. CSV 데이터팩 (로컬, 버전 관리)
    3. 원격 공급자 (추후 구현)
    """
    
    def __init__(self, db_session=None, data_dirs: List[str] = None):
        """
        Args:
            db_session: SQLAlchemy 세션 (선택)
            data_dirs: CSV 데이터팩 디렉토리 리스트 (기본: ["data"])
        """
        self.db_session = db_session
        self.data_dirs = data_dirs or ["data"]
        self._cache: Dict[int, MonsterBaseStats] = {}  # master_id -> stats
        self._name_to_id: Dict[str, int] = {}  # name (정규화) -> master_id
        
    def _load_csv(self, csv_path: str) -> Dict[int, MonsterBaseStats]:
        """CSV 파일에서 몬스터 데이터 로드"""
        monsters = {}
        if not os.path.exists(csv_path):
            return monsters
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    master_id = int(row['master_id'])
                    stats = MonsterBaseStats(
                        master_id=master_id,
                        name_ko=row.get('name_ko', ''),
                        name_en=row.get('name_en', ''),
                        element=row.get('element', ''),
                        awakened=row.get('awakened', 'true').lower() == 'true',
                        nat_stars=int(row.get('nat_stars', 4)),
                        base_hp=int(row.get('base_hp', 0)),
                        base_atk=int(row.get('base_atk', 0)),
                        base_def=int(row.get('base_def', 0)),
                        base_spd=int(row.get('base_spd', 0)),
                        base_cr=int(row.get('base_cr', BASE_CR)),
                        base_cd=int(row.get('base_cd', BASE_CD)),
                    )
                    monsters[master_id] = stats
                    
                    # 이름 매핑 (정규화)
                    for name in [stats.name_ko, stats.name_en]:
                        if name:
                            normalized = self._normalize_name(name)
                            self._name_to_id[normalized] = master_id
                except (ValueError, KeyError) as e:
                    # 잘못된 행은 스킵
                    continue
        
        return monsters
    
    def _normalize_name(self, name: str) -> str:
        """이름 정규화 (대소문자/공백 무시)"""
        return name.strip().lower().replace(' ', '').replace('-', '')
    
    def _load_from_db(self, master_id: int) -> Optional[MonsterBaseStats]:
        """DB에서 몬스터 조회"""
        if not self.db_session:
            return None
        
        try:
            from ..sw_db.models import Monster
            monster = self.db_session.query(Monster).filter(
                Monster.master_id == master_id
            ).first()
            
            if monster:
                return MonsterBaseStats(
                    master_id=monster.master_id,
                    name_ko=monster.name_ko,
                    name_en=monster.name_en,
                    element=monster.element,
                    awakened=monster.awakened,
                    nat_stars=monster.nat_stars,
                    base_hp=monster.base_hp,
                    base_atk=monster.base_atk,
                    base_def=monster.base_def,
                    base_spd=monster.base_spd,
                    base_cr=monster.base_cr or BASE_CR,
                    base_cd=monster.base_cd or BASE_CD,
                )
        except Exception:
            # DB 연결 실패 등
            pass
        
        return None
    
    def _load_from_csv(self, master_id: int) -> Optional[MonsterBaseStats]:
        """CSV에서 몬스터 조회"""
        # 모든 데이터팩 디렉토리 검색
        for data_dir in self.data_dirs:
            # CSV 파일 찾기
            csv_files = list(Path(data_dir).glob("monsters*.csv"))
            for csv_file in csv_files:
                monsters = self._load_csv(str(csv_file))
                if master_id in monsters:
                    return monsters[master_id]
        
        return None
    
    def warm_cache(self, master_ids: List[int] = None):
        """자주 쓰는 몬스터 미리 캐싱"""
        if master_ids is None:
            # 기본적으로 CSV의 모든 몬스터 캐싱
            for data_dir in self.data_dirs:
                csv_files = list(Path(data_dir).glob("monsters*.csv"))
                for csv_file in csv_files:
                    monsters = self._load_csv(str(csv_file))
                    self._cache.update(monsters)
        else:
            for master_id in master_ids:
                if master_id not in self._cache:
                    self.get(master_id=master_id)
    
    def get(self, *, master_id: int = None, name: str = None) -> Optional[MonsterBaseStats]:
        """
        몬스터 기본 스탯 조회
        
        Args:
            master_id: SWEX unit_master_id
            name: 몬스터 이름 (한글/영문, 대소문자/공백 무시)
        
        Returns:
            MonsterBaseStats 또는 None
        """
        # master_id 결정
        if master_id is None:
            if name is None:
                return None
            
            # 이름으로 master_id 조회
            normalized = self._normalize_name(name)
            master_id = self._name_to_id.get(normalized)
            if master_id is None:
                # 캐시에 없으면 CSV에서 다시 로드 시도
                for data_dir in self.data_dirs:
                    csv_files = list(Path(data_dir).glob("monsters*.csv"))
                    for csv_file in csv_files:
                        monsters = self._load_csv(str(csv_file))
                        self._cache.update(monsters)
                        for mid, stats in monsters.items():
                            normalized_ko = self._normalize_name(stats.name_ko)
                            normalized_en = self._normalize_name(stats.name_en)
                            self._name_to_id[normalized_ko] = mid
                            self._name_to_id[normalized_en] = mid
                
                master_id = self._name_to_id.get(normalized)
                if master_id is None:
                    return None
        
        # 캐시 확인
        if master_id in self._cache:
            return self._cache[master_id]
        
        # 조회 우선순위: DB → CSV
        stats = self._load_from_db(master_id)
        if stats is None:
            stats = self._load_from_csv(master_id)
        
        # 캐시에 저장
        if stats:
            self._cache[master_id] = stats
            # 이름 매핑도 업데이트
            for name in [stats.name_ko, stats.name_en]:
                if name:
                    normalized = self._normalize_name(name)
                    self._name_to_id[normalized] = master_id
        
        return stats
    
    def get_default(self) -> MonsterBaseStats:
        """기본값 반환 (몬스터 미지정 시)"""
        return MonsterBaseStats(
            master_id=0,
            name_ko="기본",
            name_en="Default",
            element="",
            awakened=False,
            nat_stars=4,
            base_hp=10000,
            base_atk=900,
            base_def=500,
            base_spd=104,
            base_cr=BASE_CR,
            base_cd=BASE_CD,
        )


# 전역 레지스트리 인스턴스 (선택적)
_global_registry: Optional[MonsterRegistry] = None


def get_registry(db_session=None, data_dirs: List[str] = None) -> MonsterRegistry:
    """전역 레지스트리 인스턴스 반환"""
    global _global_registry
    if _global_registry is None:
        _global_registry = MonsterRegistry(db_session=db_session, data_dirs=data_dirs)
    return _global_registry


def set_registry(registry: MonsterRegistry):
    """전역 레지스트리 설정"""
    global _global_registry
    _global_registry = registry

