"""DB 모델"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MonsterBase(Base):
    """몬스터 기본 스탯 테이블 (SWARFARM 데이터)"""
    __tablename__ = "monster_base"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    com2us_id = Column(Integer, unique=True, nullable=False, index=True)  # SWEX unit_master_id 매칭 키
    swarfarm_id = Column(Integer, nullable=True, index=True)  # SWARFARM API의 id
    name = Column(String(100), nullable=False)
    element = Column(String(20), nullable=False)  # fire, water, wind, light, dark
    archetype = Column(String(50), nullable=True)  # attack, defense, hp, support, etc.
    
    # 기본 스탯
    base_hp = Column(Integer, nullable=False)
    base_attack = Column(Integer, nullable=False)
    base_defense = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)
    
    # 추가 스탯
    crit_rate = Column(Float, nullable=True, default=15.0)  # 기본값 15
    crit_damage = Column(Float, nullable=True, default=50.0)  # 기본값 50
    resistance = Column(Float, nullable=True, default=0.0)
    accuracy = Column(Float, nullable=True, default=0.0)
    
    # 등급/각성 정보
    base_stars = Column(Integer, nullable=True)
    natural_stars = Column(Integer, nullable=False)
    awaken_level = Column(Integer, nullable=True, default=0)
    
    # 관계 정보
    family_id = Column(Integer, nullable=True)
    skill_group_id = Column(Integer, nullable=True)
    
    # 스킬 리스트 (JSON 문자열로 저장)
    skills_json = Column(Text, nullable=True)
    
    # 메타데이터
    updated_at_local = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 인덱스
    __table_args__ = (
        UniqueConstraint('com2us_id', name='uq_monster_base_com2us_id'),
        Index('idx_monster_base_com2us_id', 'com2us_id'),
        Index('idx_monster_base_swarfarm_id', 'swarfarm_id'),
    )
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "com2us_id": self.com2us_id,
            "swarfarm_id": self.swarfarm_id,
            "name": self.name,
            "element": self.element,
            "archetype": self.archetype,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "speed": self.speed,
            "crit_rate": self.crit_rate,
            "crit_damage": self.crit_damage,
            "resistance": self.resistance,
            "accuracy": self.accuracy,
            "base_stars": self.base_stars,
            "natural_stars": self.natural_stars,
            "awaken_level": self.awaken_level,
            "family_id": self.family_id,
            "skill_group_id": self.skill_group_id,
            "skills": json.loads(self.skills_json) if self.skills_json else [],
        }
    
    def __repr__(self):
        return f"<MonsterBase(com2us_id={self.com2us_id}, name='{self.name}')>"

