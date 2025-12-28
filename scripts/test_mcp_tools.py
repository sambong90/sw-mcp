"""MCP 서버 도구 목록 테스트"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sw_mcp_server.server import app


async def test_list_tools():
    """MCP 서버의 도구 목록 테스트"""
    print("=" * 60)
    print("MCP 서버 도구 목록 테스트")
    print("=" * 60)
    print()
    
    try:
        # list_tools 호출
        tools = await app.list_tools()
        
        print(f"[OK] 도구 개수: {len(tools)}")
        print()
        
        if len(tools) == 0:
            print("[ERROR] 도구가 없습니다!")
            return False
        
        print("등록된 도구:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}")
            print(f"     설명: {tool.description}")
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                print(f"     입력 스키마: {tool.inputSchema.get('type', 'N/A')}")
            print()
        
        print("=" * 60)
        print("[SUCCESS] 모든 도구가 정상적으로 등록되었습니다!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"[ERROR] 도구 목록 가져오기 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_list_tools())
    sys.exit(0 if success else 1)





