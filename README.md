# SW-MCP - 서머너즈워 범용 룬 빌드 엔진

서머너즈워 SWOP 수준의 정확도로 **모든 몬스터/모든 룬 세트**에 대한 빌드 탐색을 수행하는 범용 Python 라이브러리입니다.

## 프로젝트 구조

```
sw-mcp/
├── src/
│   ├── sw_core/          # 핵심 엔진 (parser, scoring, optimizer)
│   │   ├── __init__.py
│   │   ├── types.py
│   │   ├── swex_parser.py
│   │   ├── scoring.py
│   │   ├── optimizer.py
│   │   └── api.py        # Stable Python API
│   ├── sw_api/           # FastAPI (M2)
│   ├── sw_worker/        # Background jobs (M3)
│   └── sw_mcp/           # Legacy (deprecated, use sw_core)
├── ui/                   # Streamlit UI (M4)
├── tests/                # 테스트
├── docker-compose.yml    # Postgres + Redis + API + Worker
└── README.md
```

## 핵심 기능

### 1. 완전 탐색 보장 (Exhaustive Mode) ⚠️ 정확도 100%
- `mode="exhaustive"`: **정확도 100% 보장** (누락 없음)
  - Feasibility pruning만 사용 (제약조건/세트 조건 도달 불가능한 분기 제거)
  - Upper-bound pruning 사용 (top_n 모드에서만, 최적 누락 없음)
  - **Heuristic pruning/후보컷/max_candidates 제한 금지**
- `mode="fast"`: **정확도 보장 없음** (heuristic pruning 사용, 빠른 탐색)

### 2. 정확한 세트 조건
- **Target A**: Rage >= 4 AND Blade >= 2 (Fatal 거부)
- **Target B**: Fatal >= 4 AND Blade >= 2 (Rage 거부)
- 세트 보너스 정확히 적용
- `require_sets=False`: 모든 세트 허용 (SWOP-like)

### 3. 제약 조건 기반 탐색 (SWOP 스타일)
- **지원 제약조건**: SPD, CR, CD, ATK_PCT, ATK_FLAT, ATK_BONUS, ATK_TOTAL, MIN_SCORE
- **Objective**: SCORE, ATK_TOTAL, ATK_BONUS, CD, SPD
- **return_all=True**: 조건 만족하는 모든 빌드 반환 (메모리 주의)
- **allow_any_main=True**: slot 2/4/6 메인스탯 제한 해제 (preset 해제)

## 설치

### 개발 환경

```bash
cd sw-mcp
pip install -r requirements.txt
pip install -e .
```

### 환경변수 (선택)

```bash
# DB URL 설정 (기본값: sqlite:///sw_mcp.db)
export SW_MCP_DB_URL="sqlite:///sw_mcp.db"
# 또는 PostgreSQL
export SW_MCP_DB_URL="postgresql://user:password@localhost/sw_mcp"
```

### Docker Compose (프로덕션)

```bash
docker-compose up -d
```

API: http://localhost:8000
UI: `streamlit run ui/app.py` (별도 실행)

## 실행 방법

### 1. API 서버

```bash
# SQLite (개발)
uvicorn src.sw_api.main:app --reload

# 또는 Docker
docker-compose up api
```

### 2. Worker

```bash
# 직접 실행
python -m src.sw_worker.cli

# 또는 Docker
docker-compose up worker
```

### 3. UI

```bash
cd ui
streamlit run app.py
```

### 4. 데이터베이스 마이그레이션

```bash
# SQLite
alembic upgrade head

# 또는 Docker (자동 실행)
docker-compose up api
```

## 몬스터 데이터팩

### 초기 설정

1. **CSV 데이터팩 로드 (DB에 seed)**
   ```bash
   python -m src.sw_api.manage seed-monsters data/monsters_v1.csv
   ```

2. **DB에서 CSV로 export**
   ```bash
   python -m src.sw_api.manage export-monsters output.csv
   ```

### 데이터 소스 우선순위

1. **DB (운영 기본)**: `sqlite:///sw_mcp.db` 또는 설정된 DB
2. **CSV 데이터팩**: `data/monsters*.csv` (버전 관리)
3. **원격 공급자**: 추후 구현 예정

### 레지스트리 사용

```python
from src.sw_core.monster_registry import get_registry

# 레지스트리 초기화
registry = get_registry(data_dirs=["data"])

# master_id로 조회
stats = registry.get(master_id=14105)  # 루쉔
print(f"ATK: {stats.base_atk}, SPD: {stats.base_spd}")

# 이름으로 조회 (대소문자/공백 무시)
stats = registry.get(name="Lushen")
stats = registry.get(name="루쉔")
```

## 범용 룬 빌드 엔진 (Generic Optimizer)

### 핵심 개선사항

1. **모든 룬 세트 지원**
   - Stat-affecting sets: Energy, Guard, Swift, Blade, Rage, Focus, Endure, Fatal, Fight, Determination, Enhance, Accuracy, Tolerance
   - Proc sets: Violent, Will, Despair, Vampire, Nemesis, Shield, Revenge, Destroy (메타데이터만 저장, 스탯 영향 없음)
   - 데이터 기반 세트 보너스 시스템 (`set_bonuses.py`)

2. **다중 Intangible 룬 지원**
   - 여러 개의 Intangible 룬을 안전하게 처리
   - Brute-force assignment로 최적 배치 탐색
   - 모든 세트에 배치 가능 (wildcard)

3. **Exhaustive 모드 정확도 100% 보장**
   - Heuristic candidate trimming 금지
   - Upper-bound pruning 비활성화 (정확한 상한 계산 어려움)
   - Feasibility pruning만 사용 (누락 없음)
   - 테스트로 검증: brute force와 결과 일치

4. **슬롯 메인 스탯 제약 정확성**
   - Slot 1: ATK flat만 가능
   - Slot 3: DEF flat만 가능
   - Slot 5: HP flat만 가능
   - Slot 2/4/6: 특정 스탯 금지 (강제 고정 없음)

5. **DB 증분 업데이트 강화**
   - Hash 기반 변경 감지 (SHA256)
   - ETag/Last-Modified로 304 Not Modified 활용
   - 일일 스케줄러 (APScheduler) 지원
   - 상세 로깅: inserted/updated/unchanged per endpoint

6. **최소 UI (Streamlit)**
   - SWEX JSON 업로드
   - 몬스터 선택 (레지스트리 또는 수동)
   - 제약 조건 설정
   - 세트 제약 설정
   - 결과 테이블 및 상세 보기
   - CSV 내보내기

### 사용법

```python
from src.sw_core.api import run_search

# 모든 세트 지원
result = run_search(
    runes,
    monster={"name": "Lushen"},  # 또는 {"master_id": 14105}
    constraints={"SPD": 100, "CR": 100, "ATK_TOTAL": 2000},
    set_constraints={"Rage": 4, "Blade": 2},  # 선택사항
    objective="SCORE",
    mode="exhaustive",  # 정확도 100% 보장
    top_n=20
)
```

### UI 실행

```bash
streamlit run ui/app.py
```

## MCP 서버 설정 및 사용법

### MCP (Model Context Protocol) 서버

MCP 서버를 통해 LLM 클라이언트(Cursor 등)에서 룬 최적화 기능을 사용할 수 있습니다.

#### 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# MCP 패키지 설치 확인
python -c "import mcp; print('MCP OK')"
```

#### 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일 수정:
- `SW_MCP_DB_URL`: 데이터베이스 URL (기본: SQLite)
- `SW_MCP_HTTP_RPS`: HTTP 요청 제한 (기본: 2)
- `SW_MCP_ENABLE_SCHEDULER`: 스케줄러 활성화 (0 또는 1)

#### MCP 서버 실행

```bash
python -m sw_mcp_server.server
```

서버가 실행되면 다음 tools를 사용할 수 있습니다:
- `load_swex`: SWEX JSON 파일 로드
- `search_builds`: 룬 빌드 탐색
- `export_results`: 결과 내보내기
- `reset_state`: 서버 상태 초기화

#### 로컬 테스트 (MCP 클라이언트)

```bash
# MCP 클라이언트 테스트 스크립트 실행
python scripts/mcp_client_test.py --json 테오니아-1164562.json
```

이 스크립트는:
1. SWEX JSON 파일 로드
2. A) Rage 4 + Blade 2 탐색 (CR >= 100)
3. B) Fatal 4 + Blade 2 탐색 (CR >= 100)
4. 결과를 `out/` 폴더에 저장

#### Cursor에서 MCP 사용

**자동 설정 (권장):**
```bash
# Cursor MCP 설정 자동 추가
python scripts/setup_cursor_mcp.py --force
```

이 스크립트는 Cursor 설정 파일(`%APPDATA%\Cursor\User\settings.json`)에 MCP 서버 설정을 자동으로 추가합니다.

**수동 설정:**
1. Cursor 설정 파일 열기: `%APPDATA%\Cursor\User\settings.json`
2. 다음 설정 추가:
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

**사용 방법:**
1. Cursor 재시작 (설정 적용)
2. Cursor 설정에서 MCP 서버가 활성화되었는지 확인
3. 자연어로 요청:
   - "테오니아 JSON을 로드하고 루쉔 최적 빌드를 찾아줘"
   - "CR 100 이상, Rage 4 + Blade 2 조합으로 탐색해줘"
   - "SWEX 파일을 로드하고 베라드 최적 탱커 빌드를 찾아줘"

### 데이터베이스 마이그레이션

```bash
# Alembic 마이그레이션 실행
alembic upgrade head
```

### 자동 업데이트 스케줄러

#### A) OS 스케줄러 (권장)

**WSL/Linux (cron):**
```bash
# 매일 새벽 4시 실행
0 4 * * * cd /path/to/sw-mcp && . .venv/bin/activate && python -m sw_mcp.cli swarfarm-sync --all >> logs/sync.log 2>&1
```

**Windows (작업 스케줄러):**
- 작업 스케줄러에서 새 작업 생성
- 트리거: 매일 04:00
- 작업: WSL bash 실행
  ```bash
  wsl bash -c "cd /mnt/c/sw-mcp && source .venv/bin/activate && python -m sw_mcp.cli swarfarm-sync --all"
  ```

#### B) 앱 내부 스케줄러 (APScheduler)

```bash
# 환경변수 설정
export SW_MCP_ENABLE_SCHEDULER=1
export SW_MCP_SCHEDULE_HOUR=4

# 스케줄러 실행 (프로세스가 계속 실행되어야 함)
python -m sw_mcp.scheduler
```

⚠️ **주의**: 앱 내부 스케줄러는 프로세스가 실행 중일 때만 동작합니다.

## Rules-as-Data 시스템

게임 룰을 구조화된 데이터로 표현하고 버전 관리하는 시스템입니다.

### 개념

- **버전 관리**: 규칙셋은 버전 태그로 관리되며, 패치별로 업데이트 가능
- **소스 추적**: 각 규칙의 출처(SWARFARM, 오버레이 파일, 수동 입력) 추적
- **감사 가능**: 규칙 변경 이력 및 신뢰도 정보 저장
- **데이터 기반**: 하드코딩된 상수 대신 규칙셋에서 로드

### 규칙셋 스키마

규칙셋은 다음을 포함합니다:

- **RuneRules**: 슬롯별 메인/서브 합법성, 특수 규칙
- **SetRules**: 세트 보너스 수치 (2-set, 4-set)
- **GemGrindRules**: 젬/그라인드 적합성 및 캡
- **SubstatsRules**: 서브스탯 범위 (일반/고대)
- **ContentRules**: 콘텐츠별 제한 (스텁)

### 사용법

```bash
# 규칙셋 시드 (초기 생성)
python -m src.sw_mcp.cli ruleset-seed --version v1.0.0 --overlay src/sw_mcp/rules/overlays/rune_numeric_rules_v1.json

# 규칙셋 검증
python -m src.sw_mcp.cli ruleset-validate --version v1.0.0

# 규칙셋 조회
python -m src.sw_mcp.cli ruleset-show --version v1.0.0
```

### 규칙셋 업데이트

1. 오버레이 파일 수정 (`src/sw_mcp/rules/overlays/rune_numeric_rules_v1.json`)
2. 새 버전으로 시드: `ruleset-seed --version v1.1.0`
3. 현재 규칙셋 업데이트: DB의 `current_ruleset` 테이블 업데이트

### 규칙 엔진 사용

```python
from src.sw_mcp.rules.loader import load_ruleset_from_db
from src.sw_mcp.rules.engine import RulesEngine
from src.sw_mcp.db.repo import SwarfarmRepository

# 규칙셋 로드
repo = SwarfarmRepository()
ruleset = load_ruleset_from_db(repo)  # 최신 또는 특정 버전

# 엔진 생성
engine = RulesEngine(ruleset)

# 룬 검증
is_valid, error = engine.validate_rune(rune)

# 빌드 검증
is_valid, error = engine.validate_build(runes)

# 세트 보너스 적용
stats = engine.apply_set_bonus(stats, runes)
```

## SWARFARM API v2 전체 데이터 수집 시스템

SWARFARM API v2의 모든 엔드포인트를 동적으로 발견하고, 모든 리소스를 DB에 raw JSON으로 저장하는 범용 수집 시스템입니다.

### 주요 기능

- **동적 엔드포인트 발견**: API root에서 모든 엔드포인트를 자동 발견
- **Raw JSON 저장**: 정규화 없이 원본 JSON 저장 (스키마 변경에 견고)
- **증분 업데이트**: Hash 기반으로 변경된 객체만 업데이트
- **HTTP 요청 최소화**: ETag/Last-Modified로 304 Not Modified 활용
- **견고한 에러 처리**: Rate limit, 재시도, 백오프 지원
- **일일 자동화**: OS 스케줄러 또는 APScheduler 지원

### 초기 동기화

```bash
# 모든 엔드포인트 발견 및 동기화
python -m src.sw_mcp.cli swarfarm-sync --all

# 특정 엔드포인트만 동기화
python -m src.sw_mcp.cli swarfarm-sync --endpoint monsters

# 엔드포인트 목록 확인
python -m src.sw_mcp.cli swarfarm-discover
```

### 옵션

- `--db-url <URL>`: DB URL (기본값: 환경변수 `SW_MCP_DB_URL` 또는 `sqlite:///sw_mcp.db`)
- `--rps <N>`: Rate limit (초당 요청 수, 기본값: 2.0)
- `--max-pages <N>`: 최대 페이지 수 (디버그용)
- `--no-changelog`: Change log 비활성화

### 증분 업데이트 작동 방식

1. **Hash 기반 변경 감지**: 각 객체의 canonical JSON을 SHA256 해시로 저장
2. **304 Not Modified**: ETag/Last-Modified 헤더로 변경 없으면 전체 스킵
3. **Upsert 로직**:
   - 새 객체: INSERT
   - Hash 변경: UPDATE
   - Hash 동일: NO-OP (변경 없음)

### HTTP 요청 최소화

- **ETag 지원**: `If-None-Match` 헤더로 조건부 요청
- **Last-Modified 지원**: `If-Modified-Since` 헤더로 조건부 요청
- **304 응답**: 변경 없으면 전체 pagination 스킵
- **Rate Limiting**: 초당 요청 수 제한 (기본 2 RPS)

### 견고성

- **재시도**: 429/5xx 에러 시 exponential backoff + jitter (최대 6회)
- **Rate Limit**: 환경변수 `SW_MCP_HTTP_RPS`로 제어
- **방어적 파싱**: 필드 누락/스키마 변경에 견고

### 일일 자동화

#### A) OS 스케줄러 (권장)

**Linux (cron):**
```bash
# 매일 새벽 4시 실행
0 4 * * * cd /path/to/sw-mcp && python -m src.sw_mcp.cli swarfarm-sync --all
```

**Windows (Task Scheduler):**
- 작업 스케줄러에서 새 작업 생성
- 트리거: 매일 04:00
- 작업: `python -m src.sw_mcp.cli swarfarm-sync --all`

#### B) APScheduler (선택)

```bash
# 환경변수 설정
export SW_MCP_ENABLE_SCHEDULER=1
export SW_MCP_SCHEDULE_HOUR=4
export SW_MCP_SCHEDULE_TIMEZONE=Asia/Seoul

# 스케줄러 실행 (프로세스가 계속 실행되어야 함)
python -m src.sw_mcp.scheduler
```

### DB 스키마

**swarfarm_raw**: Raw JSON 저장
- `endpoint`, `object_id` (PK)
- `com2us_id` (인덱스)
- `payload_json` (canonical JSON)
- `payload_hash` (SHA256)
- `source_url`, `fetched_at`

**swarfarm_sync_state**: 엔드포인트별 동기화 상태
- `endpoint` (PK)
- `list_url`, `etag`, `last_modified`
- `last_run_at`, `last_success_at`, `last_count`, `last_error`

**swarfarm_change_log**: 변경 이력 (선택)
- `endpoint`, `object_id`, `change_type` (insert/update)
- `old_hash`, `new_hash`, `changed_at`

**swarfarm_snapshot**: 동기화 실행 요약
- 실행 시간, 통계 (inserted/updated/unchanged/errors)

## SWARFARM 몬스터 기본 스탯 DB 동기화 (레거시)

SWARFARM API를 통해 모든 몬스터의 기본 스탯을 DB에 저장하여, 룬 최적화 시 자동으로 사용할 수 있습니다.

> **참고**: 이 기능은 새로운 전체 수집 시스템으로 대체되었습니다. 위의 `swarfarm-sync --all` 명령을 사용하세요.

### 초기 동기화

```bash
# 전체 몬스터 데이터 동기화 (수천 개, 시간 소요)
python -m src.sw_mcp.sync_swarfarm monsters

# 옵션:
# --db <DB_URL>: DB URL 지정 (기본값: 환경변수 SW_MCP_DB_URL 또는 sqlite:///sw_mcp.db)
# --sleep-ms <ms>: 요청 간 슬립 시간 (기본값: 100ms, rate limit 방지)
# --max-pages <N>: 최대 페이지 수 (디버그용)
# --quiet: 상세 출력 비활성화

# 예시:
python -m src.sw_mcp.sync_swarfarm monsters --sleep-ms 200 --max-pages 5
```

### 동기화 결과

- 모든 몬스터의 기본 스탯이 `monster_base` 테이블에 저장됩니다
- `com2us_id` 기준으로 업서트되므로, 재실행 시 업데이트됩니다
- 동기화 후 룬 최적화에서 몬스터 기본 스탯을 자동으로 사용할 수 있습니다

### 몬스터 기본 스탯 조회

```python
from src.sw_mcp.monster_base import get_base_stats, get_base_stats_safe

# com2us_id로 조회 (SWEX unit_master_id와 동일)
stats = get_base_stats(14105)  # 루쉔
if stats:
    print(f"ATK: {stats['base_attack']}, SPD: {stats['speed']}")

# Fallback 지원 (DB에 없으면 기본값 사용)
stats = get_base_stats_safe(
    14105,
    fallback={"base_attack": 900, "speed": 104}
)
```

### DB 스키마

`monster_base` 테이블:
- `com2us_id` (UNIQUE): SWEX unit_master_id 매칭 키
- `swarfarm_id`: SWARFARM API의 id
- `name`, `element`, `archetype`
- `base_hp`, `base_attack`, `base_defense`, `speed`
- `crit_rate`, `crit_damage`, `resistance`, `accuracy`
- `base_stars`, `natural_stars`, `awaken_level`
- `family_id`, `skill_group_id`
- `skills_json`: 스킬 리스트 (JSON)
- `updated_at_local`: 최종 업데이트 시각

## 사용법

### 기본 API (run_search)

```python
from src.sw_core.api import run_search, run_search_from_file

# 파일에서 로드
result = run_search_from_file(
    "swex_export.json",
    target="B",
    mode="exhaustive",
    constraints={"CR": 100, "SPD": 100},
    objective="SCORE",
    top_n=10
)

print(f"Found {result['total_found']} builds")
for build in result['results']:
    print(f"Score: {build['score']}, CR: {build['cr_total']}%")
```

### 범용 빌드 탐색 (모든 몬스터/모든 세트)

```python
from src.sw_core.api import run_search
from src.sw_core.swex_parser import load_swex_json

runes = load_swex_json("swex_export.json")

# 예시 1: 몬스터 레지스트리 사용 (권장)
result = run_search(
    runes=runes,
    monster={"master_id": 14105},  # 루쉔 (base stats 자동 조회)
    constraints={"CR": 100, "SPD": 100, "ATK_TOTAL": 2000},
    set_constraints={"Fatal": 4, "Blade": 2},
    objective="SCORE",
    mode="exhaustive",
    top_n=20
)

# 이름으로도 조회 가능
result = run_search(
    runes=runes,
    monster={"name": "Lushen"},  # 또는 {"name": "루쉔"}
    constraints={"CR": 100}
)

# 예시 2: 수동 base stats 지정 (레거시 호환)
result = run_search(
    runes=runes,
    base_atk=900,
    base_spd=104,
    constraints={"CR": 100, "SPD": 100, "ATK_TOTAL": 2000},
    set_constraints={"Fatal": 4, "Blade": 2},
    objective="SCORE",
    mode="exhaustive",
    top_n=20
)

# 예시 3: 모든 세트 허용 (SWOP-like)
result = run_search(
    runes=runes,
    monster={"master_id": 14105},
    constraints={"CR": 100, "SPD": 100},
    set_constraints=None,  # 모든 세트 허용
    objective="SCORE",
    mode="exhaustive"
)

# 예시 4: 탱커 (체력/방어 중심)
result = run_search(
    runes=runes,
    monster={"name": "베라드"},  # 또는 master_id 사용
    constraints={"HP_TOTAL": 30000, "DEF_TOTAL": 1500},
    set_constraints={"Energy": 2, "Guard": 2},
    objective="EHP",
    mode="exhaustive"
)

# 예시 5: 모든 조건 만족 빌드 반환
result = run_search(
    runes=runes,
    monster={"master_id": 14105},
    constraints={"CR": 100, "SPD": 100},
    return_all=True  # 모든 빌드 반환 (메모리 주의)
)
```

### Fast Mode (정확도 보장 없음)

```python
# 빠른 탐색 (정확도 보장 없음)
result = run_search(
    runes=runes,
    target="B",
    mode="fast",  # ⚠️ 정확도 보장 없음
    max_candidates_per_slot=300,
    top_n=20
)
```

### Any Set Search (SWOP-like)

```python
# 모든 세트 허용 (세트 조건 없음)
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",
    require_sets=False,  # 세트 조건 체크 안 함
    constraints={"CR": 100, "SPD": 100},
    objective="SCORE"
)
```

### Fast Mode (성능 우선)

```python
# Heuristic pruning으로 빠른 탐색
result = run_search(
    runes=runes,
    target="B",
    mode="fast",
    max_candidates_per_slot=300,
    top_n=10
)
```

## 핵심 규칙

### 세트 ID
- **무형(Intangible) 세트**: `set_id = 25`
- 기타 세트는 표준 SWEX 형식 사용

### 기본 스탯
- **기본 치명타 확률(CR)**: 15%
- **기본 치명타 데미지(CD)**: 50%

### 세트 보너스
- **Rage 4세트**: 치명타 데미지 +40%
- **Fatal 4세트**: 공격력 +35%
- **Blade 2세트**: 치명타 확률 +12%

### 치확 조건
```
총 치확 = 기본 치확(15) + 칼날 세트 보너스(12) + 룬 치확
총 치확 >= 100% 이어야 함 (constraints에 CR이 있으면 해당 값만 체크)
```

### 무형 룬 배치
- 무형 룬은 최대 1개만 허용
- `to_Rage`, `to_Fatal`, `to_Blade`, `none` 4가지 옵션 평가
- 최적 배치 자동 선택

### 슬롯 제한
- **슬롯 1**: 서브옵에 DEF% 및 DEF+ 금지 (서브/보석 포함)
- **슬롯 2**: 메인 스탯 ATK%만 허용 (allow_any_main=True면 해제)
- **슬롯 3**: 서브옵에 ATK% 및 ATK+ 금지 (서브/보석 포함, 필수)
- **슬롯 4**: 메인 스탯 CD만 허용 (allow_any_main=True면 해제)
- **슬롯 6**: 메인 스탯 ATK%만 허용 (allow_any_main=True면 해제)
- **서브스탯**: 메인스탯과 중복 불가 (제작/가상 룬 생성 시 강제)

## 스코어 공식

```python
atk_bonus = round(base_atk * (atk_pct_total / 100.0) + atk_flat_total)
score = (cd_total * 10) + atk_bonus + 200
atk_total = base_atk + atk_bonus
```

## 테스트

```bash
# 모든 테스트 실행
python -m pytest tests/ -v

# 특정 테스트 실행
python -m pytest tests/test_generic_engine.py -v  # 범용 엔진 테스트
python -m pytest tests/test_constraint_search_accuracy.py -v  # 정확도 검증
```

### 테스트 커버리지

- **게임 룰 검증**: 슬롯별 메인/서브 제약, 중복 금지
- **범용 기능**: 모든 세트 허용, set_constraints, 범용 objectives
- **정확도 검증**: exhaustive 모드가 brute force와 완전 일치

## 개발 상태

### M1: Engine Stabilization ✅
- [x] 프로젝트 구조 재구성 (sw_core)
- [x] run_search API 구현
- [x] Exhaustive mode 검증
- [x] Unit tests 추가

### M2: DB + Import Pipeline ✅
- [x] DB 모델 생성 (Import, SearchJob, BuildResult)
- [x] Import endpoint (POST /imports)
- [x] Search job endpoint (POST /search-jobs)
- [x] Status endpoint (GET /search-jobs/{id})
- [x] Results endpoint (GET /search-jobs/{id}/results)
- [x] Alembic migration setup

### M3: Worker ✅
- [x] Background job runner (RQ + Redis)
- [x] Progress tracking
- [x] Cancellation support
- [x] Results storage

### M4: UI ✅
- [x] Streamlit UI
- [x] JSON upload screen
- [x] Search configuration screen
- [x] Results visualization
- [x] Export (JSON/CSV)

## 라이선스

MIT License
