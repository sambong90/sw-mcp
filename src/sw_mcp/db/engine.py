"""DB 엔진 설정"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# 환경변수에서 DB URL 가져오기 (기본값: SQLite)
DB_URL = os.getenv("SW_MCP_DB_URL", "sqlite:///sw_mcp.db")

_engine = None
_Session = None


def get_engine(db_url: str = None):
    """SQLAlchemy 엔진 반환 (싱글톤)"""
    global _engine
    if _engine is None:
        url = db_url or DB_URL
        _engine = create_engine(url, echo=False)
    return _engine


def get_session(db_url: str = None) -> Session:
    """DB 세션 반환"""
    global _Session
    if _Session is None:
        engine = get_engine(db_url)
        _Session = sessionmaker(bind=engine)
    
    return _Session()

