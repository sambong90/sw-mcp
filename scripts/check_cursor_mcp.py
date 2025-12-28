"""Cursor MCP 설정 진단 스크립트"""

import os
import json
import sys
from pathlib import Path

def check_cursor_mcp_setup():
    """Cursor MCP 설정 진단"""
    print("=" * 60)
    print("Cursor MCP 설정 진단")
    print("=" * 60)
    print()
    
    # 1. 설정 파일 확인
    appdata = os.getenv('APPDATA')
    if not appdata:
        print("[ERROR] APPDATA 환경 변수를 찾을 수 없습니다.")
        return False
    
    settings_path = Path(appdata) / "Cursor" / "User" / "settings.json"
    print(f"[1] 설정 파일 경로: {settings_path}")
    print(f"    존재 여부: {settings_path.exists()}")
    
    if not settings_path.exists():
        print("   [WARN] 설정 파일이 없습니다. 설정을 추가하세요.")
        return False
    
    # 2. 설정 파일 읽기
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        print("   [OK] 설정 파일 읽기 성공")
    except Exception as e:
        print(f"   [ERROR] 설정 파일 읽기 실패: {e}")
        return False
    
    # 3. mcpServers 섹션 확인
    print()
    print("[2] mcpServers 섹션 확인:")
    if "mcpServers" not in settings:
        print("   [ERROR] mcpServers 섹션이 없습니다!")
        print("   [FIX] 다음 명령 실행: python scripts/setup_cursor_mcp.py --force")
        return False
    
    mcp_servers = settings["mcpServers"]
    print(f"   [OK] mcpServers 섹션 존재 (서버 수: {len(mcp_servers)})")
    
    # 4. sw-mcp-server 설정 확인
    print()
    print("[3] sw-mcp-server 설정 확인:")
    if "sw-mcp-server" not in mcp_servers:
        print("   [ERROR] sw-mcp-server 설정이 없습니다!")
        print("   [FIX] 다음 명령 실행: python scripts/setup_cursor_mcp.py --force")
        return False
    
    server_config = mcp_servers["sw-mcp-server"]
    print("   [OK] sw-mcp-server 설정 존재")
    print(f"   - command: {server_config.get('command', 'N/A')}")
    print(f"   - args: {server_config.get('args', [])}")
    print(f"   - cwd: {server_config.get('cwd', 'N/A')}")
    print(f"   - env: {server_config.get('env', {})}")
    
    # 5. Python 경로 확인
    print()
    print("[4] Python 경로 확인:")
    python_cmd = server_config.get('command', '')
    if not python_cmd:
        print("   [ERROR] command가 설정되지 않았습니다!")
        return False
    
    if not os.path.exists(python_cmd):
        print(f"   [ERROR] Python 경로가 존재하지 않습니다: {python_cmd}")
        print("   [FIX] 다음 명령 실행: python scripts/setup_cursor_mcp.py --force")
        return False
    
    print(f"   [OK] Python 경로 존재: {python_cmd}")
    
    # 6. 작업 디렉토리 확인
    print()
    print("[5] 작업 디렉토리 확인:")
    cwd = server_config.get('cwd', '')
    if not cwd:
        print("   [ERROR] cwd가 설정되지 않았습니다!")
        return False
    
    if not os.path.exists(cwd):
        print(f"   [ERROR] 작업 디렉토리가 존재하지 않습니다: {cwd}")
        return False
    
    print(f"   [OK] 작업 디렉토리 존재: {cwd}")
    
    # 7. MCP 서버 모듈 확인
    print()
    print("[6] MCP 서버 모듈 확인:")
    src_path = Path(cwd) / "src"
    if not src_path.exists():
        print(f"   [ERROR] src 디렉토리가 없습니다: {src_path}")
        return False
    
    server_module = src_path / "sw_mcp_server" / "server.py"
    if not server_module.exists():
        print(f"   [ERROR] MCP 서버 모듈이 없습니다: {server_module}")
        return False
    
    print(f"   [OK] MCP 서버 모듈 존재: {server_module}")
    
    # 8. 모듈 실행 테스트
    print()
    print("[7] MCP 서버 모듈 실행 테스트:")
    try:
        import sys
        sys.path.insert(0, str(src_path))
        from sw_mcp_server.server import app
        print("   [OK] MCP 서버 모듈 import 성공")
    except Exception as e:
        print(f"   [ERROR] MCP 서버 모듈 import 실패: {e}")
        return False
    
    # 9. 요약
    print()
    print("=" * 60)
    print("진단 완료")
    print("=" * 60)
    print()
    print("[결과] 모든 설정이 올바르게 구성되었습니다!")
    print()
    print("[다음 단계]")
    print("1. Cursor를 완전히 종료하고 다시 시작하세요")
    print("2. Cursor 설정에서 MCP 서버가 활성화되었는지 확인하세요")
    print("   - Cursor 설정 > Features > MCP Servers")
    print("   - 또는 Cursor 채팅에서 MCP 도구 사용 가능 여부 확인")
    print("3. 자연어로 요청해보세요:")
    print("   - '테오니아 JSON을 로드하고 루쉔 최적 빌드를 찾아줘'")
    print()
    print("[참고]")
    print("- Cursor가 MCP를 지원하지 않는 버전일 수 있습니다")
    print("- Cursor의 최신 버전으로 업데이트하세요")
    print("- Cursor 설정에서 MCP 기능이 활성화되어 있는지 확인하세요")
    
    return True


if __name__ == "__main__":
    success = check_cursor_mcp_setup()
    sys.exit(0 if success else 1)





