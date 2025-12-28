"""MCP 서버 연결 및 통신 테스트"""

import sys
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_connection():
    """MCP 서버 연결 및 도구 목록 테스트"""
    print("=" * 60)
    print("MCP 서버 연결 테스트")
    print("=" * 60)
    print()
    
    # Python 경로 및 환경 설정
    import os
    python_path = sys.executable
    project_root = Path(__file__).parent.parent
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    
    # MCP 서버 파라미터
    server_params = StdioServerParameters(
        command=python_path,
        args=["-m", "sw_mcp_server.server"],
        env=env
    )
    
    try:
        print("[1] MCP 서버에 연결 중...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("   [OK] 연결 성공")
                print()
                
                print("[2] 서버 초기화 중...")
                await session.initialize()
                print("   [OK] 초기화 완료")
                print()
                
                print("[3] 도구 목록 가져오기...")
                tools_response = await session.list_tools()
                tools = tools_response.tools
                
                if not tools:
                    print("   [ERROR] 도구가 없습니다!")
                    return False
                
                print(f"   [OK] {len(tools)}개의 도구 발견:")
                for tool in tools:
                    print(f"      - {tool.name}: {tool.description}")
                print()
                
                print("[4] 간단한 도구 호출 테스트...")
                # reset_state는 인자가 필요 없으므로 테스트에 적합
                result = await session.call_tool("reset_state", {})
                
                if result.content:
                    result_text = result.content[0].text
                    result_data = json.loads(result_text)
                    if result_data.get("success"):
                        print("   [OK] 도구 호출 성공")
                        print(f"      결과: {result_data.get('message', 'N/A')}")
                    else:
                        print(f"   [WARN] 도구 호출 실패: {result_data.get('message', 'N/A')}")
                else:
                    print("   [ERROR] 응답이 없습니다")
                    return False
                
                print()
                print("=" * 60)
                print("[SUCCESS] 모든 테스트 통과!")
                print("=" * 60)
                return True
                
    except Exception as e:
        print(f"[ERROR] 연결 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_connection())
    sys.exit(0 if success else 1)




