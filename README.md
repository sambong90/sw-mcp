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

### 1. 완전 탐색 보장 (Exhaustive Mode)
- `mode="exhaustive"`: 모든 유효한 조합 탐색 (pruning 없음)
- `mode="fast"`: Heuristic pruning으로 빠른 탐색

### 2. 정확한 세트 조건
- **Target A**: Rage >= 4 AND Blade >= 2 (Fatal 거부)
- **Target B**: Fatal >= 4 AND Blade >= 2 (Rage 거부)
- 세트 보너스 정확히 적용

### 3. 제약 조건 기반 탐색
- SPD, CR, CD, ATK_PCT, ATK_FLAT, ATK_BONUS, ATK_TOTAL, MIN_SCORE
- Objective: SCORE, ATK_TOTAL, ATK_BONUS, CD, SPD
- `require_sets=False`: 모든 세트 허용 (SWOP-like)

## 설치

```bash
cd sw-mcp
pip install -e .
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

### Exhaustive Search

```python
from src.sw_core.api import run_search
from src.sw_core.swex_parser import load_swex_json

runes = load_swex_json("swex_export.json")

# 모든 조합 탐색 (최적 조합 보장)
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",  # 완전 탐색
    top_n=20
)
```

### 제약 조건 기반 탐색

```python
result = run_search(
    runes=runes,
    target="B",
    mode="exhaustive",
    constraints={
        "SPD": 100,
        "CR": 100,
        "ATK_TOTAL": 2000,
        "MIN_SCORE": 4800
    },
    objective="SCORE",
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
- **슬롯 2**: 메인 스탯 ATK%만 허용
- **슬롯 3**: 서브옵에 ATK% 및 ATK+ 금지 (필수)
- **슬롯 4**: 메인 스탯 CD만 허용
- **슬롯 6**: 메인 스탯 ATK%만 허용

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
```

## 개발 상태

### M1: Engine Stabilization ✅
- [x] 프로젝트 구조 재구성 (sw_core)
- [x] run_search API 구현
- [x] Exhaustive mode 검증
- [x] Unit tests 추가

### M2: DB + Import Pipeline (진행 예정)
- [ ] DB 모델 생성
- [ ] Import endpoint
- [ ] Search job endpoint
- [ ] Results endpoint

### M3: Worker (진행 예정)
- [ ] Background job runner
- [ ] Progress tracking
- [ ] Cancellation support

### M4: UI (진행 예정)
- [ ] Streamlit UI
- [ ] JSON upload
- [ ] Search configuration
- [ ] Results visualization

## 라이선스

MIT License
