"""DB 레포지토리"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import MonsterBase, Base
from .engine import get_engine, get_session


class MonsterRepository:
    """몬스터 레포지토리"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Args:
            session: SQLAlchemy 세션 (None이면 새로 생성)
        """
        self.session = session or get_session()
        self._own_session = session is None
    
    def upsert(self, monster_data: Dict[str, Any]) -> MonsterBase:
        """
        몬스터 데이터 업서트 (com2us_id 기준)
        
        Args:
            monster_data: SWARFARM API에서 받은 몬스터 데이터
        
        Returns:
            MonsterBase 인스턴스
        """
        # com2us_id 추출 (방어적 파싱)
        com2us_id = monster_data.get("com2us_id")
        if com2us_id is None:
            raise ValueError("com2us_id is required")
        
        # 기존 레코드 조회
        existing = self.session.query(MonsterBase).filter(
            MonsterBase.com2us_id == com2us_id
        ).first()
        
        # skills 리스트를 JSON 문자열로 변환
        skills = monster_data.get("skills", [])
        skills_json = json.dumps(skills) if skills else None
        
        if existing:
            # 업데이트
            existing.swarfarm_id = monster_data.get("id")
            existing.name = monster_data.get("name", "")
            existing.element = monster_data.get("element", "")
            existing.archetype = monster_data.get("archetype")
            existing.base_hp = monster_data.get("base_hp", 0)
            existing.base_attack = monster_data.get("base_attack", 0)
            existing.base_defense = monster_data.get("base_defense", 0)
            existing.speed = monster_data.get("speed", 0)
            existing.crit_rate = monster_data.get("crit_rate", 15.0)
            existing.crit_damage = monster_data.get("crit_damage", 50.0)
            existing.resistance = monster_data.get("resistance", 0.0)
            existing.accuracy = monster_data.get("accuracy", 0.0)
            existing.base_stars = monster_data.get("base_stars")
            existing.natural_stars = monster_data.get("natural_stars", 0)
            existing.awaken_level = monster_data.get("awaken_level", 0)
            existing.family_id = monster_data.get("family_id")
            existing.skill_group_id = monster_data.get("skill_group_id")
            existing.skills_json = skills_json
            existing.updated_at_local = datetime.utcnow()
            
            return existing
        else:
            # 새로 생성
            new_monster = MonsterBase(
                com2us_id=com2us_id,
                swarfarm_id=monster_data.get("id"),
                name=monster_data.get("name", ""),
                element=monster_data.get("element", ""),
                archetype=monster_data.get("archetype"),
                base_hp=monster_data.get("base_hp", 0),
                base_attack=monster_data.get("base_attack", 0),
                base_defense=monster_data.get("base_defense", 0),
                speed=monster_data.get("speed", 0),
                crit_rate=monster_data.get("crit_rate", 15.0),
                crit_damage=monster_data.get("crit_damage", 50.0),
                resistance=monster_data.get("resistance", 0.0),
                accuracy=monster_data.get("accuracy", 0.0),
                base_stars=monster_data.get("base_stars"),
                natural_stars=monster_data.get("natural_stars", 0),
                awaken_level=monster_data.get("awaken_level", 0),
                family_id=monster_data.get("family_id"),
                skill_group_id=monster_data.get("skill_group_id"),
                skills_json=skills_json,
            )
            self.session.add(new_monster)
            return new_monster
    
    def get_by_com2us_id(self, com2us_id: int) -> Optional[MonsterBase]:
        """com2us_id로 몬스터 조회"""
        return self.session.query(MonsterBase).filter(
            MonsterBase.com2us_id == com2us_id
        ).first()
    
    def commit(self):
        """변경사항 커밋"""
        self.session.commit()
    
    def close(self):
        """세션 종료 (자체 세션인 경우만)"""
        if self._own_session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.session.rollback()
        self.close()
    
    @staticmethod
    def create_tables(db_url: str = None):
        """테이블 생성"""
        engine = get_engine(db_url)
        Base.metadata.create_all(engine)

