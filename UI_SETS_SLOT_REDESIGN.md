# SETS / SLOT MAIN STAT UI 전면 개편 완료 보고서

## 📋 작업 개요

SETS와 SLOT MAIN STAT UI를 SWOP 스타일로 전면 개편했습니다.

## ✅ 완료된 작업

### A) SETS 선택 UI (SWOP 스타일)

#### A-1) SET 드롭다운 구현

**파일**: `ui/app_swop.py` (SETS 섹션)

1. **SET 1, SET 2, SET 3 드롭다운**
   - 좌측에 라벨, 우측에 드롭다운 배치
   - 전체 룬 세트 목록에서 선택 가능
   - "Any" 옵션 제공 (제약 없음)

2. **전체 세트 목록**
   - `SET_ID_NAME`에서 모든 세트 가져오기
   - Intangible, Unknown 제외
   - 정렬된 목록 표시
   - 예: Accuracy, Blade, Despair, Destroy, Determination, Endure, Energy, Enhance, Fatal, Fight, Focus, Guard, Nemesis, Rage, Revenge, Shield, Swift, Tolerance, Vampire, Violent, Will 등

3. **EXCLUDE 영역**
   - 멀티셀렉트로 특정 세트 제외
   - 제외된 세트는 SET1~3 드롭다운에서도 제거됨

4. **No broken sets 토글**
   - 체크박스로 활성화/비활성화
   - 최종 결과에서 세트가 깨지지 않도록 필터링

#### A-2) 세트 제약 로직 (엔진 연동)

**구현 위치**: `ui/app_swop.py` (OPTIMIZE 버튼 클릭 시)

1. **SET1~3 → set_constraints 변환**
   - SET1~3 선택값을 분석하여 `set_constraints` 딕셔너리 생성
   - 현재 구현: 세트가 2회 이상 선택되면 4-set, 1회면 2-set 요구
   - 향후 개선: 모든 가능한 조합 생성 (예: Violent+Will, Rage+Blade 등)

2. **Exclude sets 필터링**
   - 엔진 호출 전에 룬 리스트에서 제외된 세트 필터링

3. **No broken sets 후처리**
   - 최적화 결과에서 세트가 깨진 빌드 제거
   - 2-set 또는 4-set만 허용 (6-set = 4+2도 허용)

### B) SLOT 2/4/6 메인 스탯 선택 UI

#### B-1) SLOT 드롭다운 구성

**파일**: `ui/app_swop.py` (SLOT MAIN STATS 섹션)

1. **SLOT 2, SLOT 4, SLOT 6 드롭다운**
   - 각 슬롯별로 패널 구성
   - 게임 룰 기반 가능한 메인 스탯만 표시
   - "Any" 옵션 제공 (제약 없음)

2. **슬롯별 가능한 메인 스탯**
   - **Slot 2**: SPD, ATK%, ATK flat, DEF%, DEF flat, HP%, HP flat
   - **Slot 4**: CR, CD, ATK%, ATK flat, DEF%, DEF flat, HP%, HP flat, ACC, RES
   - **Slot 6**: ATK%, ATK flat, DEF%, DEF flat, HP%, HP flat, ACC, RES
   - `slot_main_is_allowed()` 함수로 게임 룰 검증

#### B-2) 엔진 연동

**구현 위치**: `ui/app_swop.py` (OPTIMIZE 버튼 클릭 시)

1. **SLOT main stat 필터링**
   - 엔진 호출 전에 룬 리스트를 필터링
   - 선택된 메인 스탯과 일치하는 룬만 유지
   - "Any" 선택 시 필터링 없음

2. **필터링 로직**
   ```python
   # Slot 2 filter
   if slot2_main != "Any":
       filtered_runes = [r for r in filtered_runes 
                       if r.slot != 2 or r.main_stat_id == target_stat_id]
   ```

## 🎨 UI 레이아웃

### SETS 섹션 (중앙 컬럼)
```
┌─────────────────┐
│     SETS        │
├─────────────────┤
│ SET 1  [드롭다운]│
│ SET 2  [드롭다운]│
│ SET 3  [드롭다운]│
├─────────────────┤
│ EXCLUDE         │
│ [멀티셀렉트]     │
├─────────────────┤
│ ☐ No broken sets│
├─────────────────┤
│ [Clear 버튼]     │
└─────────────────┘
```

### SLOT MAIN STATS 섹션 (중단)
```
┌──────────┬──────────┬──────────┐
│ SLOT 2   │ SLOT 4   │ SLOT 6   │
│ [드롭다운]│ [드롭다운]│ [드롭다운]│
└──────────┴──────────┴──────────┘
```

## 🔧 기술적 세부사항

### 세트 목록 생성
```python
from sw_core.types import SET_ID_NAME

all_sets = [name for sid, name in SET_ID_NAME.items() 
            if sid not in [25, 99] and name not in ["Intangible", "Unknown"]]
all_sets.sort()
```

### 슬롯별 메인 스탯 목록 생성
```python
from sw_core.rules import slot_main_is_allowed
from sw_core.types import STAT_ID_NAME

slot2_main_options = ["Any"]
for stat_id, stat_name in STAT_ID_NAME.items():
    if slot_main_is_allowed(2, stat_id):
        slot2_main_options.append(stat_name)
```

### 필터링 순서
1. SLOT main stat 필터링 (룬 리스트 축소)
2. Exclude sets 필터링 (룬 리스트 축소)
3. SET1~3 → set_constraints 변환
4. 엔진 호출
5. No broken sets 후처리 (결과 필터링)

## ⚠️ 현재 제한사항 및 향후 개선

### SET1~3 변환 로직
- **현재**: 단순한 휴리스틱 (세트 선택 횟수 기반)
- **향후**: 모든 가능한 조합 생성
  - 예: SET1=Violent, SET2=Will → Violent+Will 조합 생성
  - 예: SET1=Rage, SET2=Blade → Rage+Blade 조합 생성
  - 복잡한 조합도 지원 (예: Violent+Will+Shield)

### 멀티셀렉트 (Phase 2)
- **현재**: SLOT main stat은 단일 선택만 지원
- **향후**: 멀티셀렉트 지원 (예: Slot4에서 CR 또는 CD 모두 허용)

### 성능 최적화
- 대량 룬에서 필터링 성능 개선
- SET 조합 생성 최적화

## ✅ 완료 조건 체크

- [x] SET1~3 드롭다운에서 전체 세트 목록을 선택 가능
- [x] SLOT2/4/6 드롭다운에서 슬롯별 가능한 모든 메인스탯을 선택 가능
- [x] Any 옵션으로 제약 해제 가능
- [x] 이 선택값들이 실제 최적화 결과에 반영됨 (필터링/후보 제한이 동작)
- [x] Exclude sets 기능
- [x] No broken sets 토글

## 🚀 실행 방법

```bash
streamlit run ui/app_swop.py --server.port 8501
```

## 📝 사용 예시

### 예시 1: Violent + Will 조합
1. SET 1: Violent 선택
2. SET 2: Will 선택
3. SET 3: Any
4. OPTIMIZE 클릭
5. 결과: Violent+Will 조합만 표시

### 예시 2: Slot 4 CR 고정
1. SLOT 4: CR 선택
2. OPTIMIZE 클릭
3. 결과: Slot 4가 CR 메인인 빌드만 표시

### 예시 3: 특정 세트 제외
1. EXCLUDE: Revenge, Destroy 선택
2. OPTIMIZE 클릭
3. 결과: Revenge, Destroy 세트가 없는 빌드만 표시

### 예시 4: No broken sets
1. No broken sets 체크
2. OPTIMIZE 클릭
3. 결과: 세트가 깨지지 않은 빌드만 표시 (2-set 또는 4-set만)


