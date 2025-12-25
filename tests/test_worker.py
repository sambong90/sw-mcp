"""Worker tests"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.sw_worker.worker import run_search_job, enqueue_search_job
from src.sw_api.database import Base
from src.sw_api.models import Import, SearchJob, BuildResult, JobStatus
from src.sw_api.storage import storage_manager


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_import(db_session):
    """Create sample import"""
    import json
    import tempfile
    
    json_data = {
        "runes": [
            {
                "rune_id": 100,
                "slot_no": 1,
                "set_id": 5,
                "pri_eff": [4, 63],
                "sec_eff": [[9, 20, 0, 0]],
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            }
        ],
        "unit_list": []
    }
    
    # Save JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(json_data, f)
        temp_file = f.name
    
    import_record = Import(
        raw_json_path=temp_file,
        rune_count=1,
        metadata={}
    )
    db_session.add(import_record)
    db_session.commit()
    db_session.refresh(import_record)
    
    yield import_record
    
    import os
    if os.path.exists(temp_file):
        os.unlink(temp_file)


def test_run_search_job_success(db_session, sample_import):
    """Test successful job execution"""
    # Create search job
    search_job = SearchJob(
        import_id=sample_import.id,
        status=JobStatus.PENDING,
        progress=0.0,
        params={
            "target": "A",
            "mode": "exhaustive",
            "top_n": 10
        }
    )
    db_session.add(search_job)
    db_session.commit()
    db_session.refresh(search_job)
    
    # Mock database session
    with patch("src.sw_worker.worker.create_engine") as mock_engine:
        mock_engine.return_value = db_session.bind
        with patch("src.sw_worker.worker.SessionLocal") as mock_session:
            mock_session.return_value = db_session
            
            # Run job
            result = run_search_job(search_job.id)
            
            # Check result
            assert result["status"] == "completed"
            assert "total_found" in result
            
            # Check job status
            db_session.refresh(search_job)
            assert search_job.status == JobStatus.COMPLETED
            assert search_job.progress == 1.0
            
            # Check results saved
            results = db_session.query(BuildResult).filter(
                BuildResult.job_id == search_job.id
            ).all()
            assert len(results) > 0


def test_run_search_job_cancellation(db_session, sample_import):
    """Test job cancellation"""
    # Create search job
    search_job = SearchJob(
        import_id=sample_import.id,
        status=JobStatus.CANCELLED_REQUESTED,
        progress=0.0,
        params={"target": "A", "mode": "exhaustive", "top_n": 10}
    )
    db_session.add(search_job)
    db_session.commit()
    db_session.refresh(search_job)
    
    # Mock database session
    with patch("src.sw_worker.worker.create_engine") as mock_engine:
        mock_engine.return_value = db_session.bind
        with patch("src.sw_worker.worker.SessionLocal") as mock_session:
            mock_session.return_value = db_session
            
            # Run job (should be cancelled immediately)
            result = run_search_job(search_job.id)
            
            # Check result
            assert result["status"] == "cancelled"
            
            # Check job status
            db_session.refresh(search_job)
            assert search_job.status == JobStatus.CANCELLED

