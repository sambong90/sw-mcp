"""MCP Client test script for end-to-end testing"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server(json_file: str):
    """MCP 서버에 연결하여 테스트 실행"""
    
    # src 경로를 PYTHONPATH에 추가
    import os
    src_path = Path(__file__).parent.parent / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path) + os.pathsep + env.get("PYTHONPATH", "")
    
    # MCP 서버 실행 파라미터
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "sw_mcp_server.server"],
        env=env
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 서버 초기화
            await session.initialize()
            
            # 사용 가능한 tools 확인
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            print()
            
            # 1. load_swex
            print("=" * 60)
            print("1. Loading SWEX JSON...")
            print("=" * 60)
            
            load_result = await session.call_tool(
                "load_swex",
                {"json_path": json_file}
            )
            
            load_data = json.loads(load_result.content[0].text)
            print(f"Result: {load_data.get('message', '')}")
            print(f"Runes loaded: {load_data.get('rune_count', 0)}")
            print(f"Units loaded: {load_data.get('unit_count', 0)}")
            
            if not load_data.get("success"):
                print("Failed to load SWEX JSON")
                return
            
            print()
            
            # 2. Search A) Rage + Blade
            print("=" * 60)
            print("2. Searching A) Rage 4 + Blade 2 (CR >= 100)...")
            print("=" * 60)
            
            search_a_result = await session.call_tool(
                "search_builds",
                {
                    "monster": {"name": "Lushen"},
                    "constraints": {"CR": 100},
                    "set_constraints": {"Rage": 4, "Blade": 2},
                    "objective": "SCORE",
                    "mode": "exhaustive",
                    "top_n": 1
                }
            )
            
            search_a_data = json.loads(search_a_result.content[0].text)
            print(f"Result: {search_a_data.get('message', '')}")
            print(f"Builds found: {search_a_data.get('total_found', 0)}")
            
            if search_a_data.get("success") and search_a_data.get("results"):
                best_a = search_a_data["results"][0]
                stats_a = best_a.get("stats", {})
                print(f"Best score: {best_a.get('score', 0):.1f}")
                print(f"  CR: {stats_a.get('cr_total', 0):.1f}")
                print(f"  CD: {stats_a.get('cd_total', 0):.1f}")
                print(f"  ATK bonus: {stats_a.get('atk_bonus', 0)}")
            
            print()
            
            # 3. Search B) Fatal + Blade
            print("=" * 60)
            print("3. Searching B) Fatal 4 + Blade 2 (CR >= 100)...")
            print("=" * 60)
            
            search_b_result = await session.call_tool(
                "search_builds",
                {
                    "monster": {"name": "Lushen"},
                    "constraints": {"CR": 100},
                    "set_constraints": {"Fatal": 4, "Blade": 2},
                    "objective": "SCORE",
                    "mode": "exhaustive",
                    "top_n": 1
                }
            )
            
            search_b_data = json.loads(search_b_result.content[0].text)
            print(f"Result: {search_b_data.get('message', '')}")
            print(f"Builds found: {search_b_data.get('total_found', 0)}")
            
            if search_b_data.get("success") and search_b_data.get("results"):
                best_b = search_b_data["results"][0]
                stats_b = best_b.get("stats", {})
                print(f"Best score: {best_b.get('score', 0):.1f}")
                print(f"  CR: {stats_b.get('cr_total', 0):.1f}")
                print(f"  CD: {stats_b.get('cd_total', 0):.1f}")
                print(f"  ATK bonus: {stats_b.get('atk_bonus', 0)}")
            
            print()
            
            # 4. Export results
            print("=" * 60)
            print("4. Exporting results...")
            print("=" * 60)
            
            export_result = await session.call_tool(
                "export_results",
                {
                    "format": "json",
                    "output_dir": "out"
                }
            )
            
            export_data = json.loads(export_result.content[0].text)
            print(f"Result: {export_data.get('message', '')}")
            if export_data.get("file_paths"):
                print("Exported files:")
                for path in export_data["file_paths"]:
                    print(f"  - {path}")
            
            print()
            print("=" * 60)
            print("Test completed!")
            print("=" * 60)


def main():
    """Main entry point"""
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description="Test MCP server with SWEX JSON")
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Path to SWEX JSON file"
    )
    
    args = parser.parse_args()
    
    # If no file specified, try to find one automatically
    json_file = args.json
    if not json_file:
        json_files = glob.glob("*.json")
        if json_files:
            json_file = json_files[0]
            print(f"Auto-detected JSON file: {json_file}")
        else:
            print("Error: No JSON file found in current directory")
            sys.exit(1)
    
    if not Path(json_file).exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    asyncio.run(test_mcp_server(json_file))


if __name__ == "__main__":
    main()

