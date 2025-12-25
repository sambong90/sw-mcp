"""FastAPI main application"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import json

from .database import Base, engine, get_db
from .models import Import, SearchJob, BuildResult, JobStatus
from .schemas import (
    ImportResponse,
    SearchJobCreate,
    SearchJobResponse,
    BuildResultsResponse,
)
from .storage import storage_manager
from src.sw_core.swex_parser import parse_swex_json

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SW-MCP API",
    description="서머너즈워 룬 최적화 API",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "SW-MCP API", "version": "1.0.0"}


@app.post("/imports", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
async def create_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload SWEX JSON file and create import record
    
    - **file**: SWEX JSON file
    - Returns: Import record with ID and rune count
    """
    try:
        # Read and parse JSON
        content = await file.read()
        json_data = json.loads(content.decode("utf-8"))
        
        # Parse runes to get count
        runes = parse_swex_json(json_data)
        rune_count = len(runes)
        
        # Save JSON file
        json_path = storage_manager.save_json(json_data)
        
        # Create import record
        import_record = Import(
            raw_json_path=json_path,
            rune_count=rune_count,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
            }
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)
        
        return import_record
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing import: {str(e)}"
        )


@app.get("/imports/{import_id}", response_model=ImportResponse)
async def get_import(
    import_id: int,
    db: Session = Depends(get_db)
):
    """Get import record by ID"""
    import_record = db.query(Import).filter(Import.id == import_id).first()
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import {import_id} not found"
        )
    return import_record


@app.post("/search-jobs", response_model=SearchJobResponse, status_code=status.HTTP_201_CREATED)
async def create_search_job(
    job_data: SearchJobCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new search job
    
    - **import_id**: Import ID to use for search
    - **params**: Search parameters
    - Returns: Search job record (status will be PENDING)
    """
    # Verify import exists
    import_record = db.query(Import).filter(Import.id == job_data.import_id).first()
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import {job_data.import_id} not found"
        )
    
    # Create search job
    search_job = SearchJob(
        import_id=job_data.import_id,
        status=JobStatus.PENDING,
        progress=0.0,
        params=job_data.params.dict()
    )
    db.add(search_job)
    db.commit()
    db.refresh(search_job)
    
    # TODO: Enqueue job to worker (M3)
    
    return search_job


@app.get("/search-jobs/{job_id}", response_model=SearchJobResponse)
async def get_search_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get search job status by ID"""
    search_job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not search_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search job {job_id} not found"
        )
    return search_job


@app.get("/search-jobs/{job_id}/results", response_model=BuildResultsResponse)
async def get_search_results(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get search results for a completed job
    
    - **job_id**: Search job ID
    - Returns: List of build results sorted by rank
    """
    # Verify job exists
    search_job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not search_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search job {job_id} not found"
        )
    
    # Check if job is completed
    if search_job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search job {job_id} is not completed (status: {search_job.status})"
        )
    
    # Get results
    results = db.query(BuildResult).filter(
        BuildResult.job_id == job_id
    ).order_by(BuildResult.rank).all()
    
    return BuildResultsResponse(
        job_id=job_id,
        total_found=len(results),
        results=[BuildResultResponse.from_orm(r) for r in results]
    )


@app.delete("/search-jobs/{job_id}/cancel")
async def cancel_search_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel a running search job
    
    - **job_id**: Search job ID
    - Returns: Updated job status
    """
    search_job = db.query(SearchJob).filter(SearchJob.id == job_id).first()
    if not search_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search job {job_id} not found"
        )
    
    if search_job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search job {job_id} cannot be cancelled (status: {search_job.status})"
        )
    
    # Set cancellation request
    search_job.status = JobStatus.CANCELLED_REQUESTED
    db.commit()
    db.refresh(search_job)
    
    return search_job

