"""Database models for SWARFARM ingestion"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SwarfarmRaw(Base):
    """Raw JSON storage for SWARFARM objects"""
    __tablename__ = "swarfarm_raw"
    
    endpoint = Column(String(100), nullable=False, primary_key=True)
    object_id = Column(Integer, nullable=False, primary_key=True)
    com2us_id = Column(Integer, nullable=True, index=True)
    payload_json = Column(Text, nullable=False)  # Canonical JSON string
    payload_hash = Column(String(64), nullable=False, index=True)  # SHA256 hex
    source_url = Column(String(500), nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('endpoint', 'object_id', name='uq_swarfarm_raw_endpoint_object'),
        Index('idx_swarfarm_raw_endpoint', 'endpoint'),
        Index('idx_swarfarm_raw_com2us_id', 'com2us_id'),
        Index('idx_swarfarm_raw_payload_hash', 'payload_hash'),
    )
    
    def __repr__(self):
        return f"<SwarfarmRaw(endpoint='{self.endpoint}', object_id={self.object_id})>"


class SwarfarmSyncState(Base):
    """Sync state per endpoint"""
    __tablename__ = "swarfarm_sync_state"
    
    endpoint = Column(String(100), primary_key=True)
    list_url = Column(String(500), nullable=False)
    etag = Column(String(200), nullable=True)
    last_modified = Column(String(200), nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_count = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SwarfarmSyncState(endpoint='{self.endpoint}')>"


class SwarfarmChangeLog(Base):
    """Change log for insert/update events"""
    __tablename__ = "swarfarm_change_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(100), nullable=False, index=True)
    object_id = Column(Integer, nullable=False, index=True)
    change_type = Column(String(20), nullable=False)  # 'insert' or 'update'
    old_hash = Column(String(64), nullable=True)
    new_hash = Column(String(64), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("change_type IN ('insert', 'update')", name='chk_change_type'),
        Index('idx_swarfarm_change_log_endpoint', 'endpoint'),
        Index('idx_swarfarm_change_log_object_id', 'object_id'),
    )
    
    def __repr__(self):
        return f"<SwarfarmChangeLog(endpoint='{self.endpoint}', object_id={self.object_id}, type='{self.change_type}')>"


class SwarfarmSnapshot(Base):
    """Snapshot summary for each sync run"""
    __tablename__ = "swarfarm_snapshot"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    endpoints_total = Column(Integer, nullable=False)
    endpoints_changed = Column(Integer, nullable=False)
    endpoints_304 = Column(Integer, nullable=False)
    objects_inserted = Column(Integer, nullable=False)
    objects_updated = Column(Integer, nullable=False)
    objects_unchanged = Column(Integer, nullable=False)
    errors_total = Column(Integer, nullable=False)
    summary_json = Column(Text, nullable=True)  # Additional details as JSON
    
    def __repr__(self):
        return f"<SwarfarmSnapshot(id={self.id}, started_at={self.started_at})>"
