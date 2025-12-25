# M1: Engine Stabilization 완료 요약

## 완료된 작업

### 1. 프로젝트 구조 재구성
- `src/sw_mcp/` → `src/sw_core/`로 엔진 이동
- Legacy `sw_mcp`는 유지 (하위 호환성)
- 명확한 모듈 구조: `sw_core` = 핵심 엔진

### 2. Stable Python API 구현
- `run_search()`: 통합 API 함수
  - Simple optimization과 constraint-based search 모두 지원
  - Exhaustive/Fast 모드 선택
  - require_sets 옵션
- `run_search_from_json()`: JSON 데이터에서 직접 검색
- `run_search_from_file()`: 파일에서 로드하여 검색

### 3. Exhaustive Mode 검증
- Brute force와 일치하는지 검증하는 테스트 추가
- Pruning이 없는지 확인
- 모든 유효한 조합을 찾는지 검증

### 4. Unit Tests 추가
- `test_api.py`: API 함수 테스트
- `test_exhaustive_validation.py`: Exhaustive mode 검증 테스트
- 기존 테스트들 import 경로 수정 (sw_mcp → sw_core)

## API 사용 예시

### 기본 사용
```python
from src.sw_core.api import run_search_from_file

result = run_search_from_file(
    "swex_export.json",
    target="B",
    mode="exhaustive",
    constraints={"CR": 100, "SPD": 100},
    objective="SCORE",
    top_n=10
)
```

### Exhaustive vs Fast
```python
# 완전 탐색 (최적 조합 보장)
result = run_search(runes, mode="exhaustive", top_n=20)

# 빠른 탐색 (heuristic pruning)
result = run_search(runes, mode="fast", max_candidates_per_slot=300)
```

### Any Set Search
```python
# 모든 세트 허용
result = run_search(
    runes,
    require_sets=False,
    constraints={"CR": 100},
    mode="exhaustive"
)
```

## 테스트 결과

모든 테스트 통과:
- API 함수 테스트
- Exhaustive mode 검증
- Brute force 일치 검증
- 제약 조건 테스트
- Objective 정렬 테스트

## 커밋 히스토리

```
- test(m1): add API tests and exhaustive mode validation
- feat(m1): restructure to sw_core and add stable run_search API
```

## 다음 단계 (M2)

- DB 모델 생성 (Import, SearchJob, BuildResult)
- Import endpoint 구현
- Search job endpoint 구현
- Status/Results endpoint 구현

