"""MCP Server entry point"""

import sys
import json
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from .provider import (
    load_swex_tool,
    search_builds_tool,
    export_results_tool,
    reset_state_tool
)


# Create MCP server
app = Server("sw-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    try:
        print("list_tools() called", file=sys.stderr)
        tools = [
            Tool(
            name="load_swex",
            description="Load SWEX JSON file into server state",
            inputSchema={
                "type": "object",
                "properties": {
                    "json_path": {
                        "type": "string",
                        "description": "Path to SWEX JSON file"
                    },
                    "json_text": {
                        "type": "string",
                        "description": "SWEX JSON content as string (alternative to json_path)"
                    }
                }
            }
        ),
        Tool(
            name="search_builds",
            description="Search for optimal rune builds with constraints",
            inputSchema={
                "type": "object",
                "properties": {
                    "monster": {
                        "type": "object",
                        "description": "Monster info: {'name': 'Lushen'} or {'master_id': 14105}"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Stat constraints: {'CR': 100, 'SPD': 100}"
                    },
                    "objective": {
                        "type": "string",
                        "description": "Objective: SCORE, ATK_TOTAL, SPD, etc.",
                        "default": "SCORE"
                    },
                    "set_constraints": {
                        "type": "object",
                        "description": "Set constraints: {'Rage': 4, 'Blade': 2}"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Search mode: exhaustive (100% accuracy) or fast",
                        "default": "exhaustive"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top results to return",
                        "default": 20
                    }
                },
                "required": ["monster"]
            }
        ),
        Tool(
            name="export_results",
            description="Export recent search results to file (json/csv/md)",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Export format: json, csv, or md",
                        "default": "json"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory",
                        "default": "out"
                    }
                }
            }
        ),
        Tool(
            name="reset_state",
            description="Reset server state (clear loaded runes and results)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
        ]
        print(f"list_tools() returning {len(tools)} tools", file=sys.stderr)
        return tools
    except Exception as e:
        print(f"list_tools() error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return []


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if name == "load_swex":
            result = load_swex_tool(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "search_builds":
            result = search_builds_tool(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "export_results":
            result = export_results_tool(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        elif name == "reset_state":
            result = reset_state_tool(arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]


async def main():
    """Main entry point"""
    try:
        print("MCP Server initializing...", file=sys.stderr)
        async with stdio_server() as (read_stream, write_stream):
            print("MCP Server connected, waiting for requests...", file=sys.stderr)
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        print(f"MCP Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


if __name__ == "__main__":
    print("MCP Server starting...", file=sys.stderr)
    print("Available tools: load_swex, search_builds, export_results, reset_state", file=sys.stderr)
    asyncio.run(main())
