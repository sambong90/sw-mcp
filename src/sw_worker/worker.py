"""Background worker for running search jobs"""

import os
import sys
from typing import Dict, Any
from redis import Redis
from rq import Queue, Worker, Connection
from rq.job import Job
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.sw_api.database import get_db, DATABASE_URL
from src.sw_api.models import SearchJob, BuildResult, JobStatus
from src.sw_api.storage import storage_manager
from src.sw_core.api import run_search_from_json


def run_search_job(job_id: int) -> Dict[str, Any]:
    """
    Run a search job and save results
    
    Args:
        job_id: Search job ID
        
    Returns:
        Dict with job status and result count
    """
    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get job
        search_job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
        if not search_job:
            return {"error": f"Search job {job_id} not found"}
        
        # Check if cancelled
        if search_job.status == JobStatus.CANCELLED_REQUESTED:
            search_job.status = JobStatus.CANCELLED
            db.commit()
            return {"status": "cancelled", "job_id": job_id}
        
        # Update status to running
        from datetime import datetime
        search_job.status = JobStatus.RUNNING
        search_job.started_at = datetime.utcnow()
        search_job.progress = 0.0
        db.commit()
        
        # Get import and load JSON
        from src.sw_api.models import Import
        import_record = db.query(Import).filter(Import.id == search_job.import_id).first()
        if not import_record:
            search_job.status = JobStatus.FAILED
            search_job.error_message = f"Import {search_job.import_id} not found"
            db.commit()
            return {"error": search_job.error_message}
        
        json_data = storage_manager.load_json(import_record.raw_json_path)
        
        # Update progress: loading (10%)
        search_job.progress = 0.1
        db.commit()
        
        # Check cancellation again
        db.refresh(search_job)
        if search_job.status == JobStatus.CANCELLED_REQUESTED:
            search_job.status = JobStatus.CANCELLED
            db.commit()
            return {"status": "cancelled", "job_id": job_id}
        
        # Run search
        search_job.progress = 0.2
        db.commit()
        
        try:
            result = run_search_from_json(
                json_data=json_data,
                **search_job.params
            )
        except Exception as e:
            search_job.status = JobStatus.FAILED
            search_job.error_message = str(e)
            search_job.finished_at = datetime.utcnow()
            db.commit()
            return {"error": str(e), "job_id": job_id}
        
        # Check cancellation after search
        db.refresh(search_job)
        if search_job.status == JobStatus.CANCELLED_REQUESTED:
            search_job.status = JobStatus.CANCELLED
            db.commit()
            return {"status": "cancelled", "job_id": job_id}
        
        # Save results
        search_job.progress = 0.9
        db.commit()
        
        # Delete existing results for this job
        db.query(BuildResult).filter(BuildResult.job_id == job_id).delete()
        
        # Insert new results
        for rank, build in enumerate(result["results"], start=1):
            build_result = BuildResult(
                job_id=job_id,
                rank=rank,
                score=build.get("score", 0.0),
                stats_json=build.get("stats", {}),
                build_json=build
            )
            db.add(build_result)
        
        # Update job status
        search_job.status = JobStatus.COMPLETED
        search_job.progress = 1.0
        search_job.finished_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "completed",
            "job_id": job_id,
            "total_found": len(result["results"])
        }
    
    except Exception as e:
        # Mark job as failed
        if search_job:
            search_job.status = JobStatus.FAILED
            search_job.error_message = str(e)
            from datetime import datetime
            search_job.finished_at = datetime.utcnow()
            db.commit()
        return {"error": str(e), "job_id": job_id}
    
    finally:
        db.close()


def get_redis_connection():
    """Get Redis connection"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url)


def enqueue_search_job(job_id: int) -> Job:
    """
    Enqueue a search job to Redis queue
    
    Args:
        job_id: Search job ID
        
    Returns:
        RQ Job object
    """
    redis_conn = get_redis_connection()
    queue = Queue("search_jobs", connection=redis_conn)
    job = queue.enqueue(run_search_job, job_id, job_id=f"search_job_{job_id}")
    return job


if __name__ == "__main__":
    # Run worker
    redis_conn = get_redis_connection()
    with Connection(redis_conn):
        worker = Worker(["search_jobs"])
        worker.work()

