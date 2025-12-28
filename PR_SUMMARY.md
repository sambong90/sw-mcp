# Pull Request 요약

## 변경 이유

SWOP 수준의 정확도를 목표로 루쉔 최적화 코드를 리팩터링하고, 조건 기반 최적 조합 탐색 기능을 추가했습니다.

## 핵심 변경점

### 1. 정확도 개선

#### 파서 수정 (`swex_parser.py`)
- `unit_list` 읽기 지원 추가 (기존 `units`도 호환)
- `prefix_eff([stat_id, value])` 파싱 추가
- `rune_list`와 `unit_list`의 룬을 `rune_id` 기준으로 유니크 병합

#### 타입 확장 (`types.py`)
- `Rune` 클래스에 `prefix_stat_id`, `prefix_stat_value` 필드 추가
- `has_prefix`, `prefix_stat_name` 프로퍼티 추가

#### 스코어링 개선 (`scoring.py`)
- 새로운 스코어 공식 적용: `score = (cd_total * 10) + atk_bonus + 200`
- `atk_bonus = round(base_atk * (atk_pct_total/100) + atk_flat_total)`
- `atk_total = base_atk + atk_bonus` 반환
- `prefix_eff`를 CR/CD/ATK%/ATK+/SPD 합산에 포함
- SPD 계산 추가
- 무형 룬 최대 1개만 허용

### 2. 새 기능: 조건 기반 탐색

#### `search_builds` 함수 추가 (`optimizer.py`)
- DFS 기반 조합 탐색
- Pruning으로 성능 확보
- 제약 조건 지원:
  - `SPD`, `CR`, `CD`, `ATK_PCT`, `ATK_FLAT`, `ATK_BONUS`, `ATK_TOTAL`, `MIN_SCORE`
- Objective 지원:
  - `SCORE`, `ATK_TOTAL`, `ATK_BONUS`, `CD`
- `return_policy`: `top_n` 또는 `all_at_best`
- `max_results`로 결과 수 제한

#### `optimize_lushen` 개선
- `base_atk` 파라미터 추가
- 출력 포맷 개선 (prefix, spd_total, atk_total 포함)

### 3. 테스트 추가

- `test_parser.py`: `unit_list` 읽기, `prefix_eff` 파싱 테스트
- `test_scoring.py`: `prefix_eff` 합산, 새로운 스코어 공식 테스트
- `test_search_builds.py`: 제약 조건, objective 테스트

## 커밋 히스토리

```
* a6d0da8 docs: add README, changelog and implementation summary
* df33589 test: add coverage for parser/scoring/constraints
* 8efff22 feat(optimizer): add constraint-based build search with pruning
* c1261b6 fix(scoring): implement lushen score formula and set bonuses
* ec9be28 fix(parser): support unit_list and prefix_eff parsing
* 5da5c1c feat(types): add Rune class with prefix_eff support
* 03a0ae8 chore: add .gitignore
```

## 브랜치 구조

- `master`: 기본 브랜치 (.gitignore만 포함)
- `feat/parser-prefix`: 파서 및 타입 개선
- `feat/scoring-formula`: 스코어링 공식 개선
- `feat/constraints-search`: 조건 기반 탐색 기능 추가 (메인 PR 브랜치)

## 테스트 결과

모든 테스트 파일이 추가되었으며, 다음 사항을 검증합니다:

1. ✅ 파서가 `unit_list`를 읽는지
2. ✅ `prefix_eff`가 합산되는지
3. ✅ 스코어 공식이 `(cd*10)+atk_bonus+200`인지
4. ✅ 제약 조건으로 필터링되는지
5. ✅ 무형 룬 최대 1개 제한
6. ✅ 출력 포맷 요구사항 충족

## 사용 예시

```python
from src.sw_mcp.swex_parser import load_swex_json
from src.sw_mcp.optimizer import optimize_lushen, search_builds

# 기본 최적화
runes = load_swex_json("swex_export.json")
results = optimize_lushen(runes, target="B", base_atk=900, top_n=10)

# 조건 기반 탐색
results = search_builds(
    runes=runes,
    target="B",
    base_atk=900,
    base_spd=104,
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

## 성능

- `optimize_lushen`: DP 기반으로 수천 개의 룬에서도 수초 내 동작
- `search_builds`: DFS + Pruning으로 제약 조건이 많을수록 빠르게 필터링


