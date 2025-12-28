"""MCP Tool Provider implementation"""

import json
from pathlib import Path
from typing import Dict, Any, List
from sw_core.swex_parser import load_swex_json, parse_swex_json
from sw_core.api import run_search
from .state import get_state
from .schemas import (
    LoadSwexInput, LoadSwexOutput,
    SearchBuildsInput, SearchBuildsOutput,
    ExportResultsInput, ExportResultsOutput
)


def load_swex_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load SWEX JSON file into server state
    
    Args:
        input_data: {"json_path": "..."} or {"json_text": "..."}
    
    Returns:
        {"success": bool, "rune_count": int, "unit_count": int, "message": str}
    """
    try:
        input_obj = LoadSwexInput(**input_data)
        state = get_state()
        
        if input_obj.json_path:
            # Load from file
            json_path = Path(input_obj.json_path)
            if not json_path.exists():
                return LoadSwexOutput(
                    success=False,
                    rune_count=0,
                    unit_count=0,
                    message=f"File not found: {json_path}"
                ).dict()
            
            runes = load_swex_json(str(json_path))
            state.load_runes(runes, str(json_path))
            
            return LoadSwexOutput(
                success=True,
                rune_count=len(runes),
                unit_count=0,  # TODO: parse unit_list if needed
                message=f"Loaded {len(runes)} runes from {json_path.name}"
            ).dict()
        
        elif input_obj.json_text:
            # Load from JSON string
            json_data = json.loads(input_obj.json_text)
            runes = parse_swex_json(json_data)
            state.load_runes(runes, None)
            
            return LoadSwexOutput(
                success=True,
                rune_count=len(runes),
                unit_count=0,
                message=f"Loaded {len(runes)} runes from JSON text"
            ).dict()
        
        else:
            return LoadSwexOutput(
                success=False,
                rune_count=0,
                unit_count=0,
                message="Either json_path or json_text must be provided"
            ).dict()
    
    except Exception as e:
        return LoadSwexOutput(
            success=False,
            rune_count=0,
            unit_count=0,
            message=f"Error: {str(e)}"
        ).dict()


def search_builds_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for optimal rune builds
    
    Args:
        input_data: SearchBuildsInput dict
    
    Returns:
        {"success": bool, "total_found": int, "results": [...], "message": str}
    """
    try:
        input_obj = SearchBuildsInput(**input_data)
        state = get_state()
        
        if not state.runes:
            return SearchBuildsOutput(
                success=False,
                total_found=0,
                results=[],
                message="No runes loaded. Call load_swex first."
            ).dict()
        
        # Run search
        result = run_search(
            runes=state.runes,
            monster=input_obj.monster,
            constraints=input_obj.constraints,
            set_constraints=input_obj.set_constraints,
            objective=input_obj.objective,
            top_n=input_obj.top_n,
            mode=input_obj.mode
        )
        
        # Store results in state
        state.add_results(result.get("results", []))
        
        return SearchBuildsOutput(
            success=True,
            total_found=result.get("total_found", 0),
            results=result.get("results", []),
            message=f"Found {result.get('total_found', 0)} builds"
        ).dict()
    
    except Exception as e:
        return SearchBuildsOutput(
            success=False,
            total_found=0,
            results=[],
            message=f"Error: {str(e)}"
        ).dict()


def export_results_tool(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export recent search results to file
    
    Args:
        input_data: {"format": "json|csv|md", "output_dir": "out"}
    
    Returns:
        {"success": bool, "file_paths": [...], "message": str}
    """
    try:
        input_obj = ExportResultsInput(**input_data)
        state = get_state()
        
        if not state.recent_results:
            return ExportResultsOutput(
                success=False,
                file_paths=[],
                message="No results to export. Run search_builds first."
            ).dict()
        
        output_dir = Path(input_obj.output_dir or "out")
        output_dir.mkdir(exist_ok=True)
        
        file_paths = []
        
        if input_obj.format == "json":
            output_file = output_dir / "search_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(state.recent_results, f, ensure_ascii=False, indent=2)
            file_paths.append(str(output_file))
        
        elif input_obj.format == "csv":
            import csv
            output_file = output_dir / "search_results.csv"
            if state.recent_results:
                # Extract headers from first result
                first = state.recent_results[0]
                headers = ["score", "cr_total", "cd_total", "atk_total", "spd_total"]
                headers.extend([k for k in first.get("stats", {}).keys() if k not in headers])
                
                with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    for result in state.recent_results:
                        row = {"score": result.get("score", 0)}
                        row.update(result.get("stats", {}))
                        writer.writerow(row)
                file_paths.append(str(output_file))
        
        elif input_obj.format == "md":
            output_file = output_dir / "search_results.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("# Search Results\n\n")
                f.write(f"Total: {len(state.recent_results)} builds\n\n")
                for i, result in enumerate(state.recent_results[:10], 1):
                    f.write(f"## Build {i}\n\n")
                    f.write(f"- Score: {result.get('score', 0)}\n")
                    stats = result.get("stats", {})
                    f.write(f"- CR: {stats.get('cr_total', 0):.1f}\n")
                    f.write(f"- CD: {stats.get('cd_total', 0):.1f}\n")
                    f.write(f"- ATK Total: {stats.get('atk_total', 0)}\n")
                    f.write(f"- SPD: {stats.get('spd_total', 0):.1f}\n\n")
            file_paths.append(str(output_file))
        
        else:
            return ExportResultsOutput(
                success=False,
                file_paths=[],
                message=f"Unsupported format: {input_obj.format}"
            ).dict()
        
        return ExportResultsOutput(
            success=True,
            file_paths=file_paths,
            message=f"Exported {len(state.recent_results)} results to {input_obj.format}"
        ).dict()
    
    except Exception as e:
        return ExportResultsOutput(
            success=False,
            file_paths=[],
            message=f"Error: {str(e)}"
        ).dict()


def reset_state_tool(input_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Reset server state
    
    Returns:
        {"success": bool, "message": str}
    """
    try:
        state = get_state()
        state.reset()
        return {
            "success": True,
            "message": "State reset successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }
