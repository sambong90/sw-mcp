"""Repository for SWARFARM data"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from .models import SwarfarmRaw, SwarfarmSyncState, SwarfarmChangeLog, SwarfarmSnapshot, RulesetVersion, CurrentRuleset, Base
from .engine import get_engine, get_session


class SwarfarmRepository:
    """Repository for SWARFARM data operations"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Args:
            session: SQLAlchemy session (None = create new)
        """
        self.session = session or get_session()
        self._own_session = session is None
    
    def upsert_raw(
        self,
        endpoint: str,
        object_id: int,
        payload: Dict[str, Any],
        source_url: str,
        com2us_id: Optional[int] = None,
        enable_changelog: bool = True,
    ) -> Tuple[str, bool, bool]:
        """
        Upsert raw object (insert if new, update if hash changed)
        
        Args:
            endpoint: Endpoint name
            object_id: Object ID
            payload: Object payload (dict)
            source_url: Source URL
            com2us_id: Optional com2us_id from payload
            enable_changelog: Whether to log changes
        
        Returns:
            (payload_hash, is_insert, is_update) tuple
        """
        from ..swarfarm.hashing import canonicalize_json, compute_hash
        
        # Canonical JSON and hash
        canonical_json = canonicalize_json(payload)
        payload_hash = compute_hash(payload)
        
        # Check existing
        existing = self.session.query(SwarfarmRaw).filter(
            SwarfarmRaw.endpoint == endpoint,
            SwarfarmRaw.object_id == object_id
        ).first()
        
        is_insert = False
        is_update = False
        
        if existing:
            old_hash = existing.payload_hash
            if existing.payload_hash != payload_hash:
                # Update
                existing.payload_json = canonical_json
                existing.payload_hash = payload_hash
                existing.source_url = source_url
                existing.fetched_at = datetime.utcnow()
                if com2us_id is not None:
                    existing.com2us_id = com2us_id
                
                is_update = True
            else:
                # Unchanged
                pass
        else:
            # Insert
            new_raw = SwarfarmRaw(
                endpoint=endpoint,
                object_id=object_id,
                com2us_id=com2us_id,
                payload_json=canonical_json,
                payload_hash=payload_hash,
                source_url=source_url,
                fetched_at=datetime.utcnow(),
            )
            self.session.add(new_raw)
            is_insert = True
            old_hash = None
        
        # Change log
        if enable_changelog and (is_insert or is_update):
            change_type = "insert" if is_insert else "update"
            change_log = SwarfarmChangeLog(
                endpoint=endpoint,
                object_id=object_id,
                change_type=change_type,
                old_hash=old_hash,
                new_hash=payload_hash,
                changed_at=datetime.utcnow(),
            )
            self.session.add(change_log)
        
        return payload_hash, is_insert, is_update
    
    def get_sync_state(self, endpoint: str) -> Optional[SwarfarmSyncState]:
        """Get sync state for endpoint"""
        return self.session.query(SwarfarmSyncState).filter(
            SwarfarmSyncState.endpoint == endpoint
        ).first()
    
    def upsert_sync_state(
        self,
        endpoint: str,
        list_url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        last_count: Optional[int] = None,
        last_error: Optional[str] = None,
        success: bool = True,
    ):
        """Update sync state"""
        state = self.get_sync_state(endpoint)
        
        if state:
            state.list_url = list_url
            if etag is not None:
                state.etag = etag
            if last_modified is not None:
                state.last_modified = last_modified
            if last_count is not None:
                state.last_count = last_count
            if last_error is not None:
                state.last_error = last_error
            elif success:
                state.last_error = None
            state.last_run_at = datetime.utcnow()
            if success:
                state.last_success_at = datetime.utcnow()
        else:
            state = SwarfarmSyncState(
                endpoint=endpoint,
                list_url=list_url,
                etag=etag,
                last_modified=last_modified,
                last_count=last_count,
                last_error=last_error,
                last_run_at=datetime.utcnow(),
                last_success_at=datetime.utcnow() if success else None,
            )
            self.session.add(state)
    
    def create_snapshot(self) -> SwarfarmSnapshot:
        """Create new snapshot"""
        snapshot = SwarfarmSnapshot(
            started_at=datetime.utcnow(),
            endpoints_total=0,
            endpoints_changed=0,
            endpoints_304=0,
            objects_inserted=0,
            objects_updated=0,
            objects_unchanged=0,
            errors_total=0,
        )
        self.session.add(snapshot)
        return snapshot
    
    def update_snapshot(
        self,
        snapshot: SwarfarmSnapshot,
        summary: Dict[str, Any],
    ):
        """Update snapshot with final stats"""
        snapshot.finished_at = datetime.utcnow()
        snapshot.endpoints_total = summary.get("endpoints_total", 0)
        snapshot.endpoints_changed = summary.get("endpoints_changed", 0)
        snapshot.endpoints_304 = summary.get("endpoints_304", 0)
        snapshot.objects_inserted = summary.get("objects_inserted", 0)
        snapshot.objects_updated = summary.get("objects_updated", 0)
        snapshot.objects_unchanged = summary.get("objects_unchanged", 0)
        snapshot.errors_total = summary.get("errors_total", 0)
        snapshot.summary_json = json.dumps(summary)
    
    def commit(self):
        """Commit changes"""
        self.session.commit()
    
    def rollback(self):
        """Rollback changes"""
        self.session.rollback()
    
    def close(self):
        """Close session (if own session)"""
        if self._own_session:
            self.session.close()
    
    @staticmethod
    def create_tables(db_url: str = None):
        """Create tables"""
        engine = get_engine(db_url)
        Base.metadata.create_all(engine)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
