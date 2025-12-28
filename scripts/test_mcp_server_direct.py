"""MCP 서버 직접 실행 테스트"""

import sys
import subprocess
from pathlib import Path

def test_mcp_server():
    """MCP 서버를 직접 실행하여 테스트"""
    print("=" * 60)
    print("MCP 서버 직접 실행 테스트")
    print("=" * 60)
    print()
    
    # Python 경로
    python_path = sys.executable
    project_root = Path(__file__).parent.parent
    
    print(f"Python: {python_path}")
    print(f"프로젝트: {project_root}")
    print()
    
    # 환경 변수 설정
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    
    # MCP 서버 실행 (짧은 시간만)
    print("MCP 서버를 시작합니다...")
    print("(Ctrl+C로 중단하세요)")
    print()
    
    try:
        cmd = [
            python_path,
            "-m",
            "sw_mcp_server.server"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 2초 대기
        import time
        time.sleep(2)
        
        # 프로세스 종료
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        
        print("서버 출력:")
        if stdout:
            print(stdout)
        if stderr:
            print("에러 출력:")
            print(stderr)
        
        if process.returncode is None or process.returncode == 0:
            print()
            print("[OK] MCP 서버가 정상적으로 시작되었습니다!")
            return True
        else:
            print()
            print(f"[ERROR] MCP 서버 시작 실패 (코드: {process.returncode})")
            return False
            
    except KeyboardInterrupt:
        print()
        print("[INFO] 테스트 중단됨")
        return True
    except Exception as e:
        print()
        print(f"[ERROR] 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    import os
    success = test_mcp_server()
    sys.exit(0 if success else 1)





