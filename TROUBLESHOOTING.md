# Cursor MCP 서버 문제 해결 가이드

## 문제: Cursor에서 MCP 서버가 설치되지 않은 것으로 표시됨

### 1단계: 설정 확인

```bash
# 자동 진단 실행
python scripts/check_cursor_mcp.py
```

진단 결과가 모두 `[OK]`이면 설정은 올바릅니다.

### 2단계: Cursor 버전 확인

Cursor가 MCP를 지원하는 버전인지 확인하세요:
- Cursor 0.40 이상 버전에서 MCP 지원
- `Help > About Cursor`에서 버전 확인
- 최신 버전으로 업데이트: `Help > Check for Updates`

### 3단계: Cursor 설정 확인

1. **설정 파일 열기:**
   - `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"
   - 또는 직접 열기: `%APPDATA%\Cursor\User\settings.json`

2. **mcpServers 섹션 확인:**
```json
{
  "mcpServers": {
    "sw-mcp-server": {
      "command": "C:\\Users\\jbh\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
      "args": ["-m", "sw_mcp_server.server"],
      "cwd": "C:\\sw-mcp",
      "env": {
        "PYTHONPATH": "C:\\sw-mcp\\src"
      }
    }
  }
}
```

3. **설정이 없으면 추가:**
```bash
python scripts/setup_cursor_mcp.py --force
```

### 4단계: Cursor 완전 재시작

1. Cursor 완전 종료
   - 모든 Cursor 창 닫기
   - 작업 관리자에서 `Cursor.exe` 프로세스 확인 및 종료

2. Cursor 다시 시작

3. MCP 서버 확인
   - `Ctrl+Shift+P` → "MCP" 검색
   - 또는 채팅에서 MCP 도구 사용 가능 여부 확인

### 5단계: MCP 서버 수동 테스트

MCP 서버가 직접 실행되는지 확인:

```bash
# MCP 서버 직접 실행 테스트
python -m sw_mcp_server.server
```

서버가 시작되면 `MCP Server starting...` 메시지가 표시됩니다.
`Ctrl+C`로 종료하세요.

### 6단계: 대안 - Cursor 설정 UI에서 확인

1. `Ctrl+Shift+P` → "Preferences: Open Settings (UI)"
2. 검색창에 "MCP" 입력
3. MCP 관련 설정 확인:
   - "MCP: Enable" 체크
   - "MCP: Servers" 확인

### 7단계: 로그 확인

Cursor 개발자 도구에서 로그 확인:
1. `Ctrl+Shift+P` → "Developer: Toggle Developer Tools"
2. Console 탭에서 MCP 관련 오류 확인

### 일반적인 문제

#### 문제 1: Python 경로 오류
**증상:** MCP 서버가 시작되지 않음

**해결:**
```bash
# Python 경로 확인
python -c "import sys; print(sys.executable)"

# 설정 업데이트
python scripts/setup_cursor_mcp.py --force
```

#### 문제 2: 모듈을 찾을 수 없음
**증상:** `ModuleNotFoundError: No module named 'sw_mcp_server'`

**해결:**
```bash
# PYTHONPATH 확인
python -c "import sys; print('\\n'.join(sys.path))"

# src 디렉토리가 포함되어 있는지 확인
# 설정 파일의 env.PYTHONPATH 확인
```

#### 문제 3: Cursor가 설정을 읽지 않음
**증상:** 설정 파일에는 있지만 Cursor에서 보이지 않음

**해결:**
1. Cursor 완전 재시작
2. 설정 파일 JSON 구문 오류 확인
3. Cursor 버전 업데이트

### 추가 도움

문제가 계속되면:
1. 진단 스크립트 실행 결과 공유
2. Cursor 버전 정보
3. 설정 파일 내용 (민감 정보 제외)
4. Cursor 개발자 도구 콘솔 오류

### 참고

- MCP는 Cursor의 최신 기능입니다
- 일부 Cursor 버전에서는 MCP가 지원되지 않을 수 있습니다
- Cursor Pro 구독이 필요할 수 있습니다





