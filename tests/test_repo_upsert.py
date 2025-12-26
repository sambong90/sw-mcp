"""Test repository upsert logic"""

import pytest
import tempfile
import os
from src.sw_mcp.db.repo import SwarfarmRepository
from src.sw_mcp.db.models import SwarfarmRaw, SwarfarmChangeLog


@pytest.fixture
def temp_db():
    """Temporary database"""
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = db_file.name
    db_file.close()
    
    db_url = f"sqlite:///{db_path}"
    SwarfarmRepository.create_tables(db_url)
    
    yield db_url
    
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_upsert_raw_insert(temp_db):
    """Test insert"""
    repo = SwarfarmRepository()
    
    payload = {"id": 1, "name": "Test", "value": 100}
    hash_val, is_insert, is_update = repo.upsert_raw(
        "test_endpoint",
        1,
        payload,
        "https://example.com/test/1/",
        enable_changelog=True,
    )
    
    assert is_insert
    assert not is_update
    assert hash_val is not None
    
    repo.commit()
    
    # Verify in DB
    raw = repo.session.query(SwarfarmRaw).filter(
        SwarfarmRaw.endpoint == "test_endpoint",
        SwarfarmRaw.object_id == 1
    ).first()
    
    assert raw is not None
    assert raw.payload_hash == hash_val
    
    # Verify change log
    change = repo.session.query(SwarfarmChangeLog).filter(
        SwarfarmChangeLog.endpoint == "test_endpoint",
        SwarfarmChangeLog.object_id == 1
    ).first()
    
    assert change is not None
    assert change.change_type == "insert"
    
    repo.close()


def test_upsert_raw_update(temp_db):
    """Test update when hash changes"""
    from src.sw_mcp.db.engine import get_session
    repo = SwarfarmRepository(session=get_session(temp_db))
    
    # First insert
    payload1 = {"id": 1, "name": "Test", "value": 100}
    hash1, is_insert1, is_update1 = repo.upsert_raw(
        "test_endpoint",
        1,
        payload1,
        "https://example.com/test/1/",
        enable_changelog=True,
    )
    repo.commit()
    
    assert is_insert1
    assert not is_update1
    
    # Update with changed payload
    payload2 = {"id": 1, "name": "Test", "value": 200}
    hash2, is_insert2, is_update2 = repo.upsert_raw(
        "test_endpoint",
        1,
        payload2,
        "https://example.com/test/1/",
        enable_changelog=True,
    )
    repo.commit()
    
    assert not is_insert2
    assert is_update2
    assert hash1 != hash2
    
    # Verify update
    raw = repo.session.query(SwarfarmRaw).filter(
        SwarfarmRaw.endpoint == "test_endpoint",
        SwarfarmRaw.object_id == 1
    ).first()
    
    assert raw.payload_hash == hash2
    
    # Verify change log
    changes = repo.session.query(SwarfarmChangeLog).filter(
        SwarfarmChangeLog.endpoint == "test_endpoint",
        SwarfarmChangeLog.object_id == 1
    ).order_by(SwarfarmChangeLog.changed_at).all()
    
    assert len(changes) == 2
    assert changes[0].change_type == "insert"
    assert changes[1].change_type == "update"
    assert changes[1].old_hash == hash1
    assert changes[1].new_hash == hash2
    
    repo.close()


def test_upsert_raw_unchanged(temp_db):
    """Test unchanged (same hash)"""
    from src.sw_mcp.db.engine import get_session
    repo = SwarfarmRepository(session=get_session(temp_db))
    
    payload = {"id": 1, "name": "Test", "value": 100}
    
    # First insert
    hash1, is_insert1, is_update1 = repo.upsert_raw(
        "test_endpoint",
        1,
        payload,
        "https://example.com/test/1/",
        enable_changelog=True,
    )
    repo.commit()
    
    # Same payload again
    hash2, is_insert2, is_update2 = repo.upsert_raw(
        "test_endpoint",
        1,
        payload,
        "https://example.com/test/1/",
        enable_changelog=True,
    )
    repo.commit()
    
    assert hash1 == hash2
    assert not is_insert2
    assert not is_update2
    
    # Should only have one change log entry
    changes = repo.session.query(SwarfarmChangeLog).filter(
        SwarfarmChangeLog.endpoint == "test_endpoint",
        SwarfarmChangeLog.object_id == 1
    ).all()
    
    assert len(changes) == 1  # Only the insert
    
    repo.close()

