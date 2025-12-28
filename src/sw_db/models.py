"""Database models"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Monster(Base):
    """몬스터 기본 스탯 테이블"""
    __tablename__ = "monsters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    master_id = Column(Integer, unique=True, nullable=False, index=True)  # SWEX unit_master_id
    name_ko = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    element = Column(String(20), nullable=False)  # fire, water, wind, light, dark
    awakened = Column(Boolean, default=True)
    nat_stars = Column(Integer, nullable=False)  # 자연성 등급 (1-5)
    base_hp = Column(Integer, nullable=False)
    base_atk = Column(Integer, nullable=False)
    base_def = Column(Integer, nullable=False)
    base_spd = Column(Integer, nullable=False)
    base_cr = Column(Integer, default=15)  # 기본값 15
    base_cd = Column(Integer, default=50)  # 기본값 50
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Monster(master_id={self.master_id}, name_ko='{self.name_ko}', name_en='{self.name_en}')>"


# Database setup
def get_engine(db_url: str = "sqlite:///sw_mcp.db"):
    """데이터베이스 엔진 생성"""
    return create_engine(db_url, echo=False)


def get_session(db_url: str = "sqlite:///sw_mcp.db"):
    """데이터베이스 세션 생성"""
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


