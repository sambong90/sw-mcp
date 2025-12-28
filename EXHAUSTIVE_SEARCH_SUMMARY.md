# Exhaustive Search 구현 요약

## 변경 사항

### 1. scoring.py 수정

#### 세트 카운트 분리
- `count_sets()` 반환값 변경: `(rage_or_fatal_count, blade_count, intangible_count)` → `(rage_count, fatal_count, blade_count, intangible_count)`
- Rage와 Fatal을 별도로 카운트하여 정확한 세트 조건 적용

#### Target A/B 정확한 세트 조건
- **Target A**: Rage >= 4 AND Blade >= 2 (Fatal 거부)
- **Target B**: Fatal >= 4 AND Blade >= 2 (Rage 거부)
- Fatal이 포함된 조합은 target A에서 거부됨
- Rage가 포함된 조합은 target B에서 거부됨

#### 세트 보너스 정확히 적용
- Rage 4세트: CD +40 (target A만)
- Fatal 4세트: ATK% +35 (target B만)
- 각 세트가 독립적으로 카운트되어 보너스 적용

#### CR>=100 Hardcode 제거
- `score_build()`에 `require_cr_100` 파라미터 추가
- `require_sets` 파라미터 추가 (세트 조건 체크 여부)
- constraints에 CR이 있으면 `require_cr_100=False`로 설정

### 2. optimizer.py 수정

#### Exhaustive 모드 추가
- `mode="exhaustive"` (기본값): 모든 유효한 조합 탐색
  - Heuristic pruning 없음
  - Top-K truncation 없음
  - Early stop 없음
  - DFS로 모든 조합 탐색
- `mode="fast"`: 기존 동작 유지 (heuristic pruning, top-K)

#### require_sets 옵션 추가
- `require_sets=True` (기본값): target 세트 조건 필수
- `require_sets=False`: 모든 세트 허용 (SWOP-like)
  - 세트 조건 체크 없음
  - constraints만 체크

#### optimize_lushen 개선
- `mode` 파라미터 추가
- Exhaustive 모드에서는 DFS 사용
- Fast 모드에서는 기존 DP + pruning 사용

#### search_builds 개선
- `mode` 파라미터 추가
- `require_sets` 파라미터 추가
- Exhaustive 모드에서는 `max_results` 무시
- `objective="SPD"` 지원 추가
- CR>=100 hardcode 제거 (constraints에 CR이 있으면 체크 안 함)

### 3. 테스트 추가

#### test_exhaustive.py
- `test_target_a_rejects_fatal`: target A가 Fatal을 거부하는지 검증
- `test_exhaustive_matches_brute_force`: exhaustive 모드가 brute force와 일치하는지 검증
- `test_all_at_best_returns_ties`: all_at_best가 tie를 모두 반환하는지 검증
- `test_require_sets_false_allows_any_sets`: require_sets=False일 때 모든 세트 허용 검증
- `test_cr_100_not_hardcoded`: CR>=100이 hardcode되지 않았는지 검증

## 사용 예시

### Exhaustive Search (기본)
```python
from src.sw_mcp.optimizer import optimize_lushen, search_builds

# 모든 조합 탐색 (기본 모드)
results = optimize_lushen(runes, target="B", mode="exhaustive", top_n=10)

# 조건 기반 exhaustive search
results = search_builds(
    runes=runes,
    target="B",
    constraints={"CR": 100, "SPD": 100},
    objective="SCORE",
    mode="exhaustive",  # 모든 조합 탐색
    top_n=20
)
```

### Fast Mode (성능 우선)
```python
# Fast 모드 (heuristic pruning 사용)
results = optimize_lushen(
    runes, 
    target="B", 
    mode="fast",
    max_candidates_per_slot=300
)
```

### Any Set Search (SWOP-like)
```python
# 모든 세트 허용 (세트 조건 없음)
results = search_builds(
    runes=runes,
    require_sets=False,  # 세트 조건 체크 안 함
    constraints={"CR": 100, "ATK_TOTAL": 2000},
    objective="SCORE",
    mode="exhaustive"
)
```

### All at Best
```python
# 최고 점수와 동일한 모든 조합 반환
results = search_builds(
    runes=runes,
    target="B",
    objective="SCORE",
    return_policy="all_at_best",  # 모든 tie 반환
    top_n=100
)
```

## 성능 고려사항

- **Exhaustive 모드**: 모든 조합 탐색으로 정확도 100% 보장, 하지만 큰 룬 세트에서는 느릴 수 있음
- **Fast 모드**: Heuristic pruning으로 빠르지만 최적 조합을 놓칠 수 있음
- **권장**: 작은 룬 세트나 정확도가 중요한 경우 exhaustive, 큰 룬 세트나 빠른 결과가 필요한 경우 fast

## 테스트 실행

```bash
cd C:\sw-mcp
python -m pytest tests/test_exhaustive.py -v
```

## 커밋 히스토리

```
- test: add exhaustive search and set requirement tests
- feat(optimizer): add exhaustive search mode and require_sets option
- fix(scoring): separate rage/fatal counts and enforce strict set requirements
```

## GitHub

- 브랜치: `exhaustive-search`
- 원격 저장소: https://github.com/sambong90/sw-mcp
- PR 생성: https://github.com/sambong90/sw-mcp/pull/new/exhaustive-search


