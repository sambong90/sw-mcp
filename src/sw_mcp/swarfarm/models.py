"""Pydantic models for SWARFARM API responses"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class ListResponse(BaseModel):
    """Paginated list response shape"""
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Dict[str, Any]]


