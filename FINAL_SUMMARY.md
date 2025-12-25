# SW-MCP 리팩터링 최종 요약

## ✅ 완료된 작업

### [1] 정확도 필수 수정

#### 1.1 SWEX 파서 수정 (swex_parser.py)
- ✅ `unit_list` 읽기 추가 (`json_data["unit_list"]` 우선, 없으면 `units` 확인)
- ✅ `rune_list` + `unit_list[].runes`를 `rune_id` 기준으로 유니크 병합
- ✅ `prefix_eff([stat_id, value])` 파싱 추가 (0이면 없음 처리)

#### 1.2 타입 확장 (types.py)
- ✅ `Rune` 클래스에 `prefix_stat_id`, `prefix_stat_value` 필드 추가
- ✅ `has_prefix`, `prefix_stat_name` 프로퍼티 추가

#### 1.3 스코어링 변경 (scoring.py)
- ✅ BASE_CR=15, BASE_CD=50 적용
- ✅ Blade 2세트: CR +12
- ✅ Rage 4세트: CD +40 (target="A")
- ✅ Fatal 4세트: ATK% +35 (target="B")
- ✅ `atk_bonus = round(base_atk * (atk_pct_total/100) + atk_flat_total)`
- ✅ `score = (cd_total * 10) + atk_bonus + 200`
- ✅ `atk_total = base_atk + atk_bonus` 반환
- ✅ `prefix_eff`를 CR/CD/ATK%/ATK+/SPD 합산에 포함
- ✅ SPD 계산 추가

#### 1.4 무형(Intangible) 배치
- ✅ 무형 룬 최대 1개만 허용
- ✅ `to_Fatal/to_Rage/to_Blade/none` 4가지 옵션 평가
- ✅ target(A/B)에 맞게 세트 충족 + 점수 최대 배치 선택
- ✅ 결과에 `intangible_assignment` 포함

### [2] 새 기능: 조건 기반 최적 조합 탐색

#### 2.1 search_builds 함수 (optimizer.py)
- ✅ 함수 시그니처 완전 구현
- ✅ DFS 기반 조합 탐색
- ✅ Pruning으로 성능 확보
- ✅ 제약 조건 지원:
  - `SPD`, `CR`, `CD`, `ATK_PCT`, `ATK_FLAT`, `ATK_BONUS`, `ATK_TOTAL`, `MIN_SCORE`
- ✅ Objective 지원:
  - `SCORE`, `ATK_TOTAL`, `ATK_BONUS`, `CD`
- ✅ `return_policy`: `top_n` 또는 `all_at_best`
- ✅ `max_results`로 결과 수 제한

### [3] 출력 포맷
- ✅ 모든 결과에 다음 필드 포함:
  - `score`, `cr_total`, `cd_total`, `atk_pct_total`, `atk_flat_total`
  - `atk_bonus`, `atk_total`, `spd_total`
  - `intangible_assignment`
  - `slots`: `{slot_no: {rune_id, set_name, main, prefix, subs}}`

### [4] 테스트
- ✅ `test_parser.py`: `unit_list` 읽기, `prefix_eff` 파싱 테스트
- ✅ `test_scoring.py`: `prefix_eff` 합산, 새로운 스코어 공식 테스트
- ✅ `test_search_builds.py`: 제약 조건, objective 테스트

## 📁 변경된 파일 목록

1. **src/sw_mcp/types.py**
   - `Rune` 클래스에 prefix 필드 추가

2. **src/sw_mcp/swex_parser.py**
   - `parse_rune`: `prefix_eff` 파싱
   - `parse_swex_json`: `unit_list` 읽기

3. **src/sw_mcp/scoring.py**
   - `calculate_stats`: prefix 합산, SPD 추가, 새로운 atk_bonus/atk_total 계산
   - `score_build`: 새로운 스코어 공식 적용
   - `find_best_intangible_assignment`: 무형 배치 최적화

4. **src/sw_mcp/optimizer.py**
   - `DPState`: SPD 필드, prefix 처리 추가
   - `optimize_lushen`: base_atk 파라미터, 출력 포맷 개선
   - `search_builds`: 새로운 함수 추가
   - `calculate_max_remaining_stats`: Pruning용 함수
   - `check_constraints`: 제약 조건 체크 함수

5. **tests/**
   - `test_parser.py`: 테스트 추가
   - `test_scoring.py`: 테스트 추가
   - `test_search_builds.py`: 새로운 테스트 파일

## 🔑 핵심 로직

### 스코어 공식 (SWOP 스타일)
```python
atk_bonus = round(base_atk * (atk_pct_total / 100.0) + atk_flat_total)
score = (cd_total * 10) + atk_bonus + 200
atk_total = base_atk + atk_bonus
```

### prefix_eff 처리
- `prefix_eff`는 `[stat_id, value]` 형식 또는 `0`
- CR, CD, ATK%, ATK+, SPD 등 모든 스탯에 합산
- `Rune.prefix_stat_id`, `Rune.prefix_stat_value`로 저장

### 무형 룬 배치
- 무형 룬은 최대 1개만 허용
- `to_Rage`, `to_Fatal`, `to_Blade`, `none` 4가지 옵션 평가
- target에 따라 최적 배치 선택

### 조건 기반 탐색 (search_builds)
- DFS 기반 조합 탐색
- Pruning으로 성능 확보:
  - 남은 슬롯에서 얻을 수 있는 최대 스탯 계산
  - 현재 누적 + 남은 max < 제약(min)이면 가지치기

## 💻 사용 예시

### 예시 1: 기본 최적화
```python
from src.sw_mcp.swex_parser import load_swex_json
from src.sw_mcp.optimizer import optimize_lushen

# SWEX JSON 로드
runes = load_swex_json("swex_export.json")

# 루쉔 최적화 (맹공+칼날)
results = optimize_lushen(
    runes=runes,
    target="B",  # "A" (격노+칼날) 또는 "B" (맹공+칼날)
    base_atk=900,
    top_n=10
)

# 결과 출력
for i, result in enumerate(results, 1):
    print(f"#{i} Score: {result['score']:.2f}")
    print(f"  CR: {result['cr_total']:.1f}%")
    print(f"  CD: {result['cd_total']:.1f}%")
    print(f"  ATK Total: {result['atk_total']:.0f}")
    print(f"  ATK Bonus: {result['atk_bonus']:.0f}")
    print(f"  SPD: {result['spd_total']:.0f}")
    print(f"  무형 배치: {result['intangible_assignment']}")
    print()
```

### 예시 2: 조건 기반 탐색
```python
from src.sw_mcp.optimizer import search_builds

# 조건을 만족하는 조합 탐색
results = search_builds(
    runes=runes,
    target="B",
    base_atk=900,
    base_spd=104,
    constraints={
        "SPD": 100,        # 최소 속도 100
        "CR": 100,         # 최소 치확 100%
        "ATK_TOTAL": 2000, # 최소 총 공격력 2000
        "MIN_SCORE": 4800  # 최소 점수 4800
    },
    objective="SCORE",     # 점수 기준 정렬
    top_n=20,
    return_policy="top_n",
    max_results=2000
)

# 결과 출력
for i, result in enumerate(results, 1):
    print(f"#{i} Score: {result['score']:.2f}")
    print(f"  CR: {result['cr_total']:.1f}%")
    print(f"  CD: {result['cd_total']:.1f}%")
    print(f"  ATK Total: {result['atk_total']:.0f}")
    print(f"  SPD: {result['spd_total']:.0f}")
    print(f"  무형 배치: {result['intangible_assignment']}")
    
    # 슬롯별 룬 정보
    for slot, info in result['slots'].items():
        print(f"  슬롯{slot}: {info['set_name']} {info['main']}")
        if info['prefix']:
            print(f"    Prefix: {info['prefix']}")
        print(f"    Subs: {', '.join(info['subs'])}")
    print()
```

### 예시 3: ATK_TOTAL 기준 정렬
```python
results = search_builds(
    runes=runes,
    target="B",
    base_atk=900,
    constraints={
        "CR": 100,
        "CD": 150
    },
    objective="ATK_TOTAL",  # 총 공격력 기준 정렬
    top_n=10
)
```

### 예시 4: 최고 점수와 동일한 모든 조합
```python
results = search_builds(
    runes=runes,
    target="B",
    base_atk=900,
    constraints={"CR": 100},
    objective="SCORE",
    return_policy="all_at_best",  # 최고 점수와 동일한 모든 조합
    top_n=50
)
```

## 📊 결과 포맷 예시

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
            "subs": ["CR 20", "CD 7", "SPD 5"]
        },
        2: {
            "rune_id": 12346,
            "set_name": "Fatal",
            "main": "ATK% 63",
            "prefix": "",
            "subs": ["CR 20", "CD 7"]
        },
        # ... 슬롯 3~6
    }
}
```

## ⚡ 성능 고려사항

1. **optimize_lushen**: DP 기반으로 수천 개의 룬에서도 수초 내 동작
2. **search_builds**: DFS + Pruning으로 제약 조건이 많을수록 빠르게 필터링
3. **max_results**: 기본값 2000으로 제한하여 메모리 사용량 제어

## ✅ 검증 완료

- ✅ 파서가 `unit_list`를 읽는지
- ✅ `prefix_eff`가 합산되는지
- ✅ 스코어 공식이 `(cd*10)+atk_bonus+200`인지
- ✅ 제약 조건으로 필터링되는지
- ✅ 무형 룬 최대 1개 제한
- ✅ 출력 포맷 요구사항 충족

## 🎯 목표 달성

- ✅ SWOP 수준의 정확도 달성
- ✅ 조건 기반 최적 조합 탐색 구현
- ✅ 파서/스코어링 정확도 개선
- ✅ 모든 요구사항 충족

