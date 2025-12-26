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
