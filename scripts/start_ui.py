"""Streamlit UI 시작 스크립트"""

import subprocess
import sys
import os
from pathlib import Path

def start_ui():
    """Streamlit UI 시작"""
    ui_dir = Path(__file__).parent.parent / "ui"
    app_file = ui_dir / "app.py"
    
    if not app_file.exists():
        print(f"[ERROR] UI 파일을 찾을 수 없습니다: {app_file}")
        return False
    
    print("=" * 60)
    print("Streamlit UI 시작")
    print("=" * 60)
    print()
    print(f"UI 디렉토리: {ui_dir}")
    print(f"앱 파일: {app_file}")
    print()
    print("Streamlit 서버를 시작합니다...")
    print("브라우저에서 http://localhost:8501 에 접속하세요")
    print()
    print("종료하려면 Ctrl+C를 누르세요")
    print("=" * 60)
    print()
    
    # Streamlit 실행
    os.chdir(ui_dir)
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\nUI를 종료합니다.")
        return True
    except Exception as e:
        print(f"[ERROR] UI 시작 실패: {e}")
        return False


if __name__ == "__main__":
    start_ui()


