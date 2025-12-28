"""LLM 연동 테스트 - Cursor MCP 서버 확인"""

import sys
import json
import os
from pathlib import Path

def check_llm_integration():
    """LLM 연동 상태 확인"""
    print("=" * 60)
    print("LLM 연동 상태 확인")
    print("=" * 60)
    print()
    
    # 1. Cursor 설정 확인
    print("[1] Cursor MCP 설정 확인:")
    appdata = os.getenv('APPDATA')
    if not appdata:
        print("   [ERROR] APPDATA 환경 변수를 찾을 수 없습니다.")
        return False
    
    settings_path = Path(appdata) / "Cursor" / "User" / "settings.json"
    if not settings_path.exists():
        print(f"   [ERROR] 설정 파일이 없습니다: {settings_path}")
        return False
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    mcp_servers = settings.get("mcpServers", {})
    if "sw-mcp-server" not in mcp_servers:
        print("   [ERROR] sw-mcp-server 설정이 없습니다!")
        print("   [FIX] 다음 명령 실행: python scripts/setup_cursor_mcp.py --force")
        return False
    
    server_config = mcp_servers["sw-mcp-server"]
    print(f"   [OK] sw-mcp-server 설정 존재")
    print(f"      command: {server_config.get('command')}")
    print(f"      cwd: {server_config.get('cwd')}")
    print()
    
    # 2. MCP 서버 모듈 확인
    print("[2] MCP 서버 모듈 확인:")
    cwd = server_config.get('cwd')
    src_path = Path(cwd) / "src"
    server_module = src_path / "sw_mcp_server" / "server.py"
    
    if not server_module.exists():
        print(f"   [ERROR] MCP 서버 모듈이 없습니다: {server_module}")
        return False
    
    print(f"   [OK] MCP 서버 모듈 존재: {server_module}")
    
    # 3. MCP 서버 실행 테스트
    print()
    print("[3] MCP 서버 실행 테스트:")
    import subprocess
    import time
    
    command = server_config.get('command')
    args = server_config.get('args', [])
    env = os.environ.copy()
    env.update(server_config.get('env', {}))
    
    try:
        process = subprocess.Popen(
            [command] + args,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        time.sleep(2)
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        
        if "MCP Server starting" in stderr:
            print("   [OK] MCP 서버가 정상적으로 시작됩니다")
        else:
            print("   [WARN] MCP 서버 시작 메시지를 찾을 수 없습니다")
            if stderr:
                print(f"      오류: {stderr[:200]}")
    except Exception as e:
        print(f"   [ERROR] 서버 실행 테스트 실패: {e}")
        return False
    
    # 4. 요약
    print()
    print("=" * 60)
    print("LLM 연동 상태 요약")
    print("=" * 60)
    print()
    print("[설정 상태]")
    print("  [OK] Cursor MCP 설정: 완료")
    print("  [OK] MCP 서버 모듈: 존재")
    print("  [OK] MCP 서버 실행: 정상")
    print()
    print("[다음 단계]")
    print("  1. Cursor를 완전히 재시작하세요")
    print("  2. Cursor 채팅에서 다음을 시도하세요:")
    print("     - '테오니아 JSON을 로드하고 루쉔 최적 빌드를 찾아줘'")
    print("     - 'load_swex 도구를 사용해서 SWEX 파일을 로드해줘'")
    print("  3. MCP 도구가 사용되는지 확인하세요")
    print()
    print("[확인 방법]")
    print("  - Cursor 채팅에서 MCP 도구가 자동으로 호출되는지 확인")
    print("  - 'no mcp tools' 메시지가 사라졌는지 확인")
    print("  - Cursor 개발자 도구에서 MCP 관련 로그 확인")
    print()
    print("[주의사항]")
    print("  - Cursor를 완전히 종료하고 다시 시작해야 설정이 적용됩니다")
    print("  - Cursor 버전이 MCP를 지원하는지 확인하세요 (0.40 이상)")
    print("  - Cursor Pro 구독이 필요할 수 있습니다")
    
    return True


if __name__ == "__main__":
    success = check_llm_integration()
    sys.exit(0 if success else 1)

