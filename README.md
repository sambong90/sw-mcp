# SW-MCP - 서머너즈워 룬 최적화 엔진

서머너즈워 SWOP 수준의 정확도로 루쉔 최적화를 수행하는 Python 라이브러리입니다.

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

### Exhaustive Search (정확도 100% 보장)

```python
from src.sw_core.api import run_search
from src.sw_core.swex_parser import load_swex_json

runes = load_swex_json("swex_export.json")

# 모든 조합 탐색 (정확도 100%, 누락 없음)
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",  # 정확도 100% 보장
    top_n=20
)
```

### 제약 조건 기반 탐색 (SWOP 스타일)

```python
# 여러 제약조건과 objective 지정
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",  # 정확도 100% 보장
    constraints={
        "SPD": 100,
        "CR": 100,
        "ATK_TOTAL": 2000,
        "MIN_SCORE": 4800
    },
    objective="SCORE",  # 또는 "ATK_TOTAL", "ATK_BONUS", "CD", "SPD"
    top_n=20
)

# 모든 조건 만족 빌드 반환 (return_all=True)
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",
    constraints={"CR": 100, "SPD": 100},
    return_all=True  # 모든 빌드 반환 (메모리 주의)
)

# Preset 해제 (allow_any_main=True)
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",
    allow_any_main=True  # slot 2/4/6 메인스탯 제한 해제
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
python -m pytest tests/test_api.py -v
python -m pytest tests/test_exhaustive.py -v
python -m pytest tests/test_constraint_search_accuracy.py -v  # 정확도 검증
```

### 정확도 검증

`test_constraint_search_accuracy.py`는 exhaustive 모드가 brute force와 완전히 일치함을 검증합니다:
- 작은 샘플에서 모든 조합을 brute force로 탐색
- exhaustive 모드 결과와 비교하여 완전 일치 확인
- 제약조건, objective, return_all 등 모든 기능 검증

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
