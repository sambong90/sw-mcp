"""Pydantic schemas for MCP server input/output"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class LoadSwexInput(BaseModel):
    """Input for load_swex tool"""
    json_path: Optional[str] = Field(None, description="Path to SWEX JSON file")
    json_text: Optional[str] = Field(None, description="SWEX JSON content as string")
    
    class Config:
        json_schema_extra = {
            "example": {
                "json_path": "테오니아-1164562.json"
            }
        }


class LoadSwexOutput(BaseModel):
    """Output from load_swex tool"""
    success: bool
    rune_count: int
    unit_count: int
    message: str


class SearchBuildsInput(BaseModel):
    """Input for search_builds tool"""
    monster: Dict[str, Any] = Field(..., description="Monster info: {'name': 'Lushen'} or {'master_id': 14105}")
    constraints: Optional[Dict[str, float]] = Field(None, description="Stat constraints: {'CR': 100, 'SPD': 100}")
    objective: str = Field("SCORE", description="Objective: SCORE, ATK_TOTAL, SPD, etc.")
    set_constraints: Optional[Dict[str, int]] = Field(None, description="Set constraints: {'Rage': 4, 'Blade': 2}")
    mode: str = Field("exhaustive", description="Search mode: exhaustive (100% accuracy) or fast")
    top_n: int = Field(20, description="Number of top results to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "monster": {"name": "Lushen"},
                "constraints": {"CR": 100},
                "objective": "SCORE",
                "set_constraints": {"Rage": 4, "Blade": 2},
                "mode": "exhaustive",
                "top_n": 1
            }
        }


class SearchBuildsOutput(BaseModel):
    """Output from search_builds tool"""
    success: bool
    total_found: int
    results: List[Dict[str, Any]]
    message: str


class ExportResultsInput(BaseModel):
    """Input for export_results tool"""
    format: str = Field("json", description="Export format: json, csv, or md")
    output_dir: Optional[str] = Field("out", description="Output directory")
    
    class Config:
        json_schema_extra = {
            "example": {
                "format": "json",
                "output_dir": "out"
            }
        }


class ExportResultsOutput(BaseModel):
    """Output from export_results tool"""
    success: bool
    file_paths: List[str]
    message: str
