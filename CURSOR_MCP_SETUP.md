# Cursor MCP 서버 설정 가이드

## 자동 설정 (권장)

프로젝트 루트에서 다음 명령을 실행하세요:

```bash
python scripts/setup_cursor_mcp.py --force
```

이 스크립트는 다음을 자동으로 수행합니다:
- Cursor 설정 파일 위치 확인 (`%APPDATA%\Cursor\User\settings.json`)
- MCP 서버 설정 자동 추가
- 프로젝트 경로 및 PYTHONPATH 자동 설정

## 설정 확인

설정이 제대로 추가되었는지 확인:

```bash
# 자동 진단 스크립트 실행 (권장)
python scripts/check_cursor_mcp.py

# 또는 수동 확인
python -c "import json, os; path = os.path.join(os.getenv('APPDATA'), 'Cursor', 'User', 'settings.json'); print(json.dumps(json.load(open(path, 'r', encoding='utf-8')).get('mcpServers', {}), indent=2))"
```

## 수동 설정

자동 설정이 작동하지 않는 경우, 수동으로 설정할 수 있습니다:

1. **Cursor 설정 파일 열기:**
   - Windows: `%APPDATA%\Cursor\User\settings.json`
   - 또는 Cursor에서 `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"

2. **다음 설정 추가:**
```json
{
  "mcpServers": {
    "sw-mcp-server": {
      "command": "python",
      "args": ["-m", "sw_mcp_server.server"],
      "cwd": "C:\\sw-mcp",
      "env": {
        "PYTHONPATH": "C:\\sw-mcp\\src"
      }
    }
  }
}
```

**주의:** `cwd` 경로를 실제 프로젝트 경로로 변경하세요.

## 사용 방법

1. **Cursor 재시작**
   - 설정 변경 후 Cursor를 완전히 종료하고 다시 시작하세요

2. **MCP 서버 확인**
   - Cursor 설정에서 MCP 서버가 활성화되었는지 확인
   - 또는 채팅에서 MCP 도구가 사용 가능한지 확인

3. **자연어로 요청**
   - "테오니아 JSON을 로드하고 루쉔 최적 빌드를 찾아줘"
   - "CR 100 이상, Rage 4 + Blade 2 조합으로 탐색해줘"
   - "SWEX 파일을 로드하고 베라드 최적 탱커 빌드를 찾아줘"

## 사용 가능한 MCP 도구

- `load_swex`: SWEX JSON 파일 로드
- `search_builds`: 룬 빌드 탐색 (제약 조건, 세트 조건, 목표 등)
- `export_results`: 검색 결과 내보내기 (JSON/CSV/MD)
- `reset_state`: 서버 상태 초기화

## 문제 해결

### Cursor에서 MCP 서버가 보이지 않는 경우

**1. Cursor 버전 확인**
- Cursor가 MCP를 지원하는 버전인지 확인하세요
- 최신 버전으로 업데이트하세요: `Help > Check for Updates`

**2. Cursor 설정에서 MCP 활성화 확인**
- `Ctrl+Shift+P` → "Preferences: Open Settings (UI)"
- "MCP" 또는 "Model Context Protocol" 검색
- MCP 기능이 활성화되어 있는지 확인

**3. Cursor 재시작**
- 설정 변경 후 Cursor를 완전히 종료하고 다시 시작
- 작업 관리자에서 모든 Cursor 프로세스가 종료되었는지 확인

**4. 설정 파일 위치 확인**
- Cursor가 다른 설정 파일을 사용할 수 있습니다
- `Ctrl+Shift+P` → "Preferences: Open User Settings (JSON)"으로 실제 설정 파일 확인

**5. 수동 설정 확인**
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

**6. 진단 스크립트 실행**
```bash
python scripts/check_cursor_mcp.py
```

### MCP 서버가 연결되지 않는 경우

1. **Python 경로 확인:**
   ```bash
   python -m sw_mcp_server.server
   ```
   이 명령이 오류 없이 실행되어야 합니다.

2. **의존성 확인:**
   ```bash
   pip install -r requirements.txt
   ```

3. **프로젝트 경로 확인:**
   - `cwd` 설정이 실제 프로젝트 루트 경로와 일치하는지 확인
   - Windows에서는 백슬래시(`\\`)를 사용해야 합니다

4. **PYTHONPATH 확인:**
   - `src` 디렉토리가 PYTHONPATH에 포함되어 있는지 확인

### 설정이 적용되지 않는 경우

1. Cursor를 완전히 종료하고 다시 시작
2. 설정 파일의 JSON 구문 오류 확인
3. Cursor 로그 확인 (개발자 도구)

## 추가 정보

- MCP 서버는 stdio를 통해 통신합니다
- 서버는 요청 시 자동으로 시작됩니다
- 여러 Cursor 창에서 동시에 사용할 수 있습니다


