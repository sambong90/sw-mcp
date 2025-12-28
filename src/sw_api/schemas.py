"""Pydantic schemas for API requests/responses"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from .models import JobStatus


class ImportCreate(BaseModel):
    """Request schema for creating an import"""
    pass  # File upload handled separately


class ImportResponse(BaseModel):
    """Response schema for import"""
    id: int
    created_at: datetime
    rune_count: int
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SearchParams(BaseModel):
    """Search parameters"""
    target: str = Field(default="B", description="Target build: 'A' (Rage+Blade) or 'B' (Fatal+Blade)")
    mode: str = Field(default="exhaustive", description="Search mode: 'exhaustive' or 'fast'")
    constraints: Optional[Dict[str, float]] = Field(default=None, description="Minimum constraints (e.g., {'CR': 100, 'SPD': 100})")
    objective: str = Field(default="SCORE", description="Sort objective: 'SCORE', 'ATK_TOTAL', 'ATK_BONUS', 'CD', 'SPD'")
    top_n: int = Field(default=20, ge=1, le=1000, description="Number of top results to return")
    return_policy: str = Field(default="top_n", description="Return policy: 'top_n' or 'all_at_best'")
    base_atk: int = Field(default=900, ge=1, description="Base attack stat")
    base_spd: int = Field(default=104, ge=1, description="Base speed stat")
    require_sets: bool = Field(default=True, description="Require target set conditions")
    max_candidates_per_slot: int = Field(default=300, ge=1, description="Max candidates per slot (fast mode)")
    max_results: int = Field(default=2000, ge=1, description="Max results limit (fast mode)")


class SearchJobCreate(BaseModel):
    """Request schema for creating a search job"""
    import_id: int = Field(description="Import ID to use for search")
    params: SearchParams = Field(description="Search parameters")


class SearchJobResponse(BaseModel):
    """Response schema for search job"""
    id: int
    import_id: int
    status: JobStatus
    progress: float
    params: Dict[str, Any]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BuildResultResponse(BaseModel):
    """Response schema for build result"""
    id: int
    job_id: int
    rank: int
    score: float
    stats_json: Dict[str, Any]
    build_json: Dict[str, Any]
    
    class Config:
        from_attributes = True


class SearchResultsResponse(BaseModel):
    """Response schema for search results"""
    job_id: int
    total_found: int
    results: List[BuildResultResponse]


