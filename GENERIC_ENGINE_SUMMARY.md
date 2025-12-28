# 범용 엔진 리팩터링 완료 요약

## 완료된 작업

### 1. Rules 모듈 분리 (rules.py)
- **Single Source of Truth**: 모든 룬 검증 규칙을 rules.py에 집중
- `validate_rune(rune)`: 룬 1개가 룰에 맞는지 검증
- `validate_build(runes_6)`: 6개 조합이 룰에 맞는지 검증
- `slot_main_is_allowed(slot, main_stat_id)`: 슬롯별 메인스탯 허용 여부
- `slot_sub_is_allowed(slot, main_stat_id, sub_stat_id)`: 슬롯별 서브스탯 허용 여부 (메인 중복 금지 포함)
- `slot_prefix_is_allowed(slot, prefix_stat_id)`: 슬롯별 접두옵 허용 여부

### 2. 게임 룰 구현
- **Slot 2**: 메인에서 CD/CR/RES/ACC 선택 불가
- **Slot 4**: 메인에서 SPD/ACC/RES 선택 불가
- **Slot 6**: 메인에서 SPD/CD/CR 선택 불가
- **Slot 3**: 공격력 옵션(ATK+, ATK%) 메인/서브/접두 모두 금지
- **Slot 1**: 방어력 옵션(DEF+, DEF%) 메인/서브/접두 모두 금지
- **모든 슬롯**: 서브/접두의 stat_id가 메인 stat_id와 동일하면 금지

### 3. 하드코딩 제거
- ❌ 제거: `target="A"/"B"` 하드코딩
- ❌ 제거: `slot 2/4/6 메인 고정` (ATK%/CD)
- ❌ 제거: `require_sets=True` 기본값
- ✅ 추가: `set_constraints={"Rage": 4, "Blade": 2}` 범용 dict
- ✅ 추가: `base_hp`, `base_def` 파라미터

### 4. 범용 Scoring
- `calculate_stats()`: 모든 스탯 계산 (HP, DEF, RES, ACC 포함)
- `score_build()`: 범용 API (base_atk/spd/hp/def, constraints, set_constraints, objective)
- `get_objective_value()`: 플러그인 형태의 objective 함수
- 지원 objectives: SCORE, ATK_TOTAL, EHP, SPD, DAMAGE_PROXY 등

### 5. 범용 Optimizer
- `search_builds()`: 범용 API
  - `set_constraints=None`: 모든 세트 허용 (기본)
  - `set_constraints={"Rage": 4, "Blade": 2}`: 특정 세트 조건
  - `constraints`: 범용 제약조건 (CR, CD, SPD, ATK_TOTAL, HP_TOTAL, DEF_TOTAL, MIN_SCORE)
  - `objective`: 범용 목표함수
- Exhaustive 모드: 정확도 100% 보장 (heuristic pruning 없음)

### 6. API 업데이트
- `run_search()`: 범용 API
  - `base_atk`, `base_spd`, `base_hp`, `base_def` 파라미터
  - `set_constraints` 파라미터 (target 제거)
  - 범용 constraints/objectives 지원

## 주요 변경 파일

1. **src/sw_core/rules.py** (신규)
   - 모든 룬 검증 규칙

2. **src/sw_core/optimizer.py** (대폭 수정)
   - `filter_rune_by_slot()`: rules.py 기반으로 변경
   - `search_builds()`: 범용 API로 변경
   - `DPState`: 범용 스탯 추적

3. **src/sw_core/scoring.py** (대폭 수정)
   - `calculate_stats()`: 모든 스탯 계산
   - `score_build()`: 범용 API
   - `get_objective_value()`: 플러그인 형태

4. **src/sw_core/api.py** (수정)
   - `run_search()`: 범용 API

5. **tests/test_generic_engine.py** (신규)
   - 범용 엔진 테스트

## 사용 예시

### 루쉔 (공격형)
```python
result = run_search(
    runes=runes,
    base_atk=900,
    base_spd=104,
    constraints={"CR": 100, "SPD": 100, "ATK_TOTAL": 2000},
    set_constraints={"Fatal": 4, "Blade": 2},
    objective="SCORE",
    mode="exhaustive"
)
```

### 탱커 (체력/방어 중심)
```python
result = run_search(
    runes=runes,
    base_hp=15000,
    base_def=800,
    constraints={"HP_TOTAL": 30000, "DEF_TOTAL": 1500},
    set_constraints={"Energy": 2, "Guard": 2},
    objective="EHP",
    mode="exhaustive"
)
```

### 모든 세트 허용 (SWOP-like)
```python
result = run_search(
    runes=runes,
    base_atk=900,
    constraints={"CR": 100, "SPD": 100},
    set_constraints=None,  # 모든 세트 허용
    objective="SCORE",
    mode="exhaustive"
)
```

## 테스트 결과

- ✅ 슬롯별 메인/서브 제약 테스트 통과
- ✅ 슬롯 1/3 추가 룰 테스트 통과
- ✅ 서브/메인 중복 금지 테스트 통과
- ✅ require_sets=False (모든 세트 허용) 테스트 통과
- ✅ set_constraints 테스트 통과
- ✅ 범용 objectives 테스트 통과
- ✅ Exhaustive vs Brute Force 정확도 검증 통과

## GitHub 상태

- 브랜치: `feature/generic-engine`
- 커밋: 3개 (rules, refactor, test)
- Push: 완료

PR 생성 링크:
```
https://github.com/sambong90/sw-mcp/pull/new/feature/generic-engine
```


