"""Cursor MCP 서버 디버깅 스크립트"""

import sys
import os
import subprocess
import json
from pathlib import Path

def debug_mcp_server():
    """MCP 서버를 Cursor가 실행하는 방식으로 테스트"""
    print("=" * 60)
    print("Cursor MCP 서버 디버깅")
    print("=" * 60)
    print()
    
    # Cursor 설정에서 MCP 서버 설정 읽기
    appdata = os.getenv('APPDATA')
    settings_path = Path(appdata) / "Cursor" / "User" / "settings.json"
    
    if not settings_path.exists():
        print("[ERROR] Cursor 설정 파일을 찾을 수 없습니다.")
        return False
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    mcp_servers = settings.get("mcpServers", {})
    if "sw-mcp-server" not in mcp_servers:
        print("[ERROR] sw-mcp-server 설정이 없습니다.")
        return False
    
    server_config = mcp_servers["sw-mcp-server"]
    print("[1] Cursor 설정 확인:")
    print(f"   command: {server_config.get('command')}")
    print(f"   args: {server_config.get('args')}")
    print(f"   cwd: {server_config.get('cwd')}")
    print(f"   env: {server_config.get('env', {})}")
    print()
    
    # Cursor가 실행하는 명령 재현
    command = server_config.get('command')
    args = server_config.get('args', [])
    cwd = server_config.get('cwd')
    env = os.environ.copy()
    env.update(server_config.get('env', {}))
    
    print("[2] MCP 서버 실행 테스트:")
    print(f"   명령: {command} {' '.join(args)}")
    print(f"   작업 디렉토리: {cwd}")
    print(f"   환경 변수: {env.get('PYTHONPATH', 'Not set')}")
    print()
    
    try:
        # MCP 서버를 짧은 시간 실행
        process = subprocess.Popen(
            [command] + args,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 3초 대기
        import time
        time.sleep(3)
        
        # 프로세스 종료
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        
        print("[3] 서버 출력:")
        if stderr:
            print("   STDERR:")
            for line in stderr.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        if stdout:
            print("   STDOUT:")
            for line in stdout.split('\n'):
                if line.strip():
                    print(f"      {line}")
        
        if "MCP Server starting" in stderr:
            print()
            print("[OK] MCP 서버가 정상적으로 시작되었습니다!")
            return True
        else:
            print()
            print("[ERROR] MCP 서버 시작 메시지를 찾을 수 없습니다.")
            if stderr:
                print("   오류가 발생했을 수 있습니다. 위의 STDERR를 확인하세요.")
            return False
            
    except Exception as e:
        print(f"[ERROR] 서버 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_mcp_server()
    sys.exit(0 if success else 1)



