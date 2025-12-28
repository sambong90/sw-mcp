# 구현 요약

## 변경된 파일 목록

1. **src/sw_mcp/types.py**
   - `Rune` 클래스에 `prefix_stat_id`, `prefix_stat_value` 필드 추가
   - `has_prefix`, `prefix_stat_name` 프로퍼티 추가

2. **src/sw_mcp/swex_parser.py**
   - `parse_rune`: `prefix_eff` 파싱 추가
   - `parse_swex_json`: `unit_list` 읽기 추가 (기존 `units`도 지원)

3. **src/sw_mcp/scoring.py**
   - `calculate_stats`: `prefix_eff` 합산, SPD 추가, 새로운 `atk_bonus`/`atk_total` 계산
   - `score_build`: 새로운 스코어 공식 적용 `(cd_total * 10) + atk_bonus + 200`
   - 무형 룬 최대 1개만 허용
   - `base_atk` 파라미터 추가

4. **src/sw_mcp/optimizer.py**
   - `DPState`: SPD 필드 추가, `prefix_eff` 처리 추가
   - `optimize_lushen`: `base_atk` 파라미터 추가, 출력 포맷 개선 (prefix, spd_total, atk_total 포함)
   - `search_builds`: 새로운 함수 추가 (조건 기반 탐색)
   - `calculate_max_remaining_stats`: Pruning용 최대 스탯 계산
   - `check_constraints`: 제약 조건 체크 및 pruning

5. **tests/**
   - `test_parser.py`: `unit_list` 읽기, `prefix_eff` 파싱 테스트 추가
   - `test_scoring.py`: `prefix_eff` 합산, 새로운 스코어 공식 테스트 추가
   - `test_search_builds.py`: 새로운 파일 (제약 조건, objective 테스트)

## 핵심 로직

### 1. 스코어 공식 (SWOP 스타일)
```python
atk_bonus = round(base_atk * (atk_pct_total / 100.0) + atk_flat_total)
score = (cd_total * 10) + atk_bonus + 200
atk_total = base_atk + atk_bonus
```

### 2. prefix_eff 처리
- `prefix_eff`는 `[stat_id, value]` 형식 또는 `0`
- CR, CD, ATK%, ATK+, SPD 등 모든 스탯에 합산
- `Rune.prefix_stat_id`, `Rune.prefix_stat_value`로 저장

### 3. 무형 룬 배치
- 무형 룬은 최대 1개만 허용
- `to_Rage`, `to_Fatal`, `to_Blade`, `none` 4가지 옵션 평가
- target에 따라 최적 배치 선택

### 4. 조건 기반 탐색 (search_builds)
- DFS 기반 조합 탐색
- Pruning으로 성능 확보:
  - 남은 슬롯에서 얻을 수 있는 최대 스탯 계산
  - 현재 누적 + 남은 max < 제약(min)이면 가지치기
- 지원 제약 조건:
  - `SPD`, `CR`, `CD`, `ATK_PCT`, `ATK_FLAT`, `ATK_BONUS`, `ATK_TOTAL`, `MIN_SCORE`
- 지원 objective:
  - `SCORE`, `ATK_TOTAL`, `ATK_BONUS`, `CD`

## 사용 예시

### 기본 최적화
```python
from src.sw_mcp.swex_parser import load_swex_json
from src.sw_mcp.optimizer import optimize_lushen

runes = load_swex_json("swex_export.json")
results = optimize_lushen(
    runes=runes,
    target="B",  # 맹공+칼날
    base_atk=900,
    top_n=10
)

for result in results:
    print(f"Score: {result['score']}")
    print(f"CR: {result['cr_total']}%")
    print(f"CD: {result['cd_total']}%")
    print(f"ATK Total: {result['atk_total']}")
    print(f"SPD: {result['spd_total']}")
```

### 조건 기반 탐색
```python
from src.sw_mcp.optimizer import search_builds

results = search_builds(
    runes=runes,
    target="B",
    base_atk=900,
    base_spd=104,
    constraints={
        "SPD": 100,      # 최소 속도 100
        "CR": 100,       # 최소 치확 100%
        "ATK_TOTAL": 2000,  # 최소 총 공격력 2000
        "MIN_SCORE": 4800   # 최소 점수 4800
    },
    objective="SCORE",   # 점수 기준 정렬
    top_n=20,
    return_policy="top_n"
)

for result in results:
    print(f"Score: {result['score']}")
    print(f"ATK Total: {result['atk_total']}")
    print(f"SPD: {result['spd_total']}")
    print(f"Intangible: {result['intangible_assignment']}")
```

### 결과 포맷
```python
{
    "score": 4956.0,
    "cr_total": 100.0,
    "cd_total": 200.0,
    "atk_pct_total": 350.0,
    "atk_flat_total": 100.0,
    "atk_bonus": 3250.0,
    "atk_total": 4150.0,
    "spd_total": 120.0,
    "intangible_assignment": "to_Fatal",
    "slots": {
        1: {
            "rune_id": 12345,
            "set_name": "Fatal",
            "main": "ATK% 63",
            "prefix": "CR 5",
            "subs": ["CR 20", "CD 7"]
        },
        # ... 슬롯 2~6
    }
}
```

## 성능 고려사항

1. **optimize_lushen**: DP 기반으로 수천 개의 룬에서도 수초 내 동작
2. **search_builds**: DFS + Pruning으로 제약 조건이 많을수록 빠르게 필터링
3. **max_results**: 기본값 2000으로 제한하여 메모리 사용량 제어

## 향후 개선 사항

1. Pruning 로직 개선: 세트 보너스를 더 정확히 고려
2. DP 기반 search_builds: 제약 조건이 없을 때 DP 사용
3. Gem/Grind 모드 구현
4. 병렬 처리 지원


