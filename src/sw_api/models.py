"""Database models"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base


class JobStatus(str, enum.Enum):
    """Search job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CANCELLED_REQUESTED = "cancelled_requested"


class Import(Base):
    """Rune import record"""
    __tablename__ = "imports"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    raw_json_path = Column(String(512), nullable=False)  # Path to stored JSON file
    rune_count = Column(Integer, nullable=False)
    metadata = Column(JSON, nullable=True)  # Additional metadata (SWEX version, etc.)
    
    def __repr__(self):
        return f"<Import(id={self.id}, rune_count={self.rune_count}, created_at={self.created_at})>"


class SearchJob(Base):
    """Search job record"""
    __tablename__ = "search_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(Integer, nullable=False, index=True)  # Foreign key to Import
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    params = Column(JSON, nullable=False)  # Search parameters
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SearchJob(id={self.id}, status={self.status}, progress={self.progress})>"


class BuildResult(Base):
    """Build result record"""
    __tablename__ = "build_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)  # Foreign key to SearchJob
    rank = Column(Integer, nullable=False)  # Rank in results (1-based)
    score = Column(Float, nullable=False)
    stats_json = Column(JSON, nullable=False)  # Full stats dict
    build_json = Column(JSON, nullable=False)  # Full build dict (slots, runes, etc.)
    
    # Index for efficient querying
    __table_args__ = (
        {"sqlite_autoincrement": True} if "sqlite" in str(Base.metadata.bind.url) else {}
    )
    
    def __repr__(self):
        return f"<BuildResult(job_id={self.job_id}, rank={self.rank}, score={self.score})>"

