"""Cursor MCP 서버 설정 자동 추가 스크립트"""

import os
import json
import sys
from pathlib import Path

def get_cursor_settings_path():
    """Cursor 설정 파일 경로 찾기"""
    appdata = os.getenv('APPDATA')
    if not appdata:
        return None
    
    # Windows: %APPDATA%\Cursor\User\settings.json
    settings_path = Path(appdata) / "Cursor" / "User" / "settings.json"
    
    # 설정 디렉토리가 없으면 생성
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    return settings_path


def get_project_root():
    """프로젝트 루트 경로"""
    return Path(__file__).parent.parent.absolute()


def setup_mcp_config(force=False):
    """Cursor MCP 설정 추가"""
    settings_path = get_cursor_settings_path()
    if not settings_path:
        print("[ERROR] Cursor 설정 디렉토리를 찾을 수 없습니다.")
        print("   Windows: %APPDATA%\\Cursor\\User\\settings.json")
        return False
    
    project_root = get_project_root()
    
    # 기존 설정 로드
    settings = {}
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except Exception as e:
            print(f"[WARN] 기존 설정 파일 읽기 실패: {e}")
            print("   새 설정 파일을 생성합니다.")
    
    # Python 경로 확인
    import sys
    python_path = sys.executable
    
    # MCP 서버 설정 추가
    mcp_config = {
        "command": python_path,
        "args": [
            "-m",
            "sw_mcp_server.server"
        ],
        "cwd": str(project_root),
        "env": {
            "PYTHONPATH": str(project_root / "src")
        }
    }
    
    # mcpServers 섹션이 없으면 생성
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}
    
    # 기존 설정 확인
    if "sw-mcp-server" in settings["mcpServers"] and not force:
        print("[INFO] 기존 'sw-mcp-server' 설정이 있습니다.")
        print("   자동으로 덮어쓰기합니다.")
    
    # 설정 추가
    settings["mcpServers"]["sw-mcp-server"] = mcp_config
    
    # 설정 저장
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Cursor MCP 설정이 추가되었습니다!")
        print(f"   설정 파일: {settings_path}")
        print(f"   서버 이름: sw-mcp-server")
        print(f"   작업 디렉토리: {project_root}")
        print()
        print("[NEXT STEPS] 다음 단계:")
        print("   1. Cursor를 재시작하세요")
        print("   2. Cursor 설정에서 MCP 서버가 활성화되었는지 확인하세요")
        print("   3. 자연어로 요청해보세요:")
        print("      - '테오니아 JSON을 로드하고 루쉔 최적 빌드를 찾아줘'")
        print("      - 'CR 100 이상, Rage 4 + Blade 2 조합으로 탐색해줘'")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 설정 파일 저장 실패: {e}")
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cursor MCP 서버 설정 자동 추가")
    parser.add_argument("--force", action="store_true", help="기존 설정을 강제로 덮어쓰기")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Cursor MCP 서버 설정 자동 추가")
    print("=" * 60)
    print()
    
    success = setup_mcp_config(force=args.force)
    
    if success:
        print()
        print("=" * 60)
        print("설정 완료!")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("설정 실패")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

