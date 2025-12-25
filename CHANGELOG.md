# 변경 사항

## 주요 수정 사항

### 1. types.py
- **SET_ID_NAME에 25:Intangible 추가**: 실제 JSON에서 무형 세트는 `set_id=25`를 사용
- **99:Intangible 제거**: 99는 "Unknown"으로 처리
- **BASE_CR=15, BASE_CD=50 상수 추가**: 기본 스탯 정의
- **세트 보너스 상수 추가**: RAGE_4SET_CD, FATAL_4SET_ATK_PCT, BLADE_2SET_CR

### 2. swex_parser.py
- **무형 판정 수정**: `rune.intangible = (set_id == 25)`로 변경
- **sec_eff 파싱 개선**: `base + grind`를 최종 값으로 저장
- **룬 중복 제거 개선**: `rune_list`와 `unit_list`의 룬을 `rune_id` 기준으로 유니크하게 병합
- **seen_rune_ids에 rune_list도 포함**: 중복 없이 완전히 병합

### 3. scoring.py
- **기본 치확 15 적용**: `BASE_CR=15`를 `cr_total` 계산에 반영
- **칼날 세트 보너스 12 적용**: Blade 2세트 이상일 때 `BLADE_2SET_CR=12` 추가
- **무형 세트 보정 로직 수정**: 
  - 무형 1개가 Rage/Fatal과 Blade에 동시에 기여하지 않도록 수정
  - `find_best_intangible_assignment` 함수로 최적 배치 선택
- **Fatal 4세트 보너스 로직 개선**: 무형 배치를 고려하여 Fatal 보너스 적용
- **치확 조건**: `(BASE_CR + BladeBonus + runeCR) >= 100`으로 판정

### 4. optimizer.py
- **DP 기반 재구현**: 
  - 슬롯별로 상태를 전파하는 DP 알고리즘
  - 동일 상태에서 최선의 스탯만 유지하여 메모리 효율성 확보
- **슬롯 조건 강화**:
  - 슬롯2: 메인 ATK%만 허용
  - 슬롯3: 서브옵 ATK% 및 ATK+ 금지
  - 슬롯4: 메인 CD만 허용
  - 슬롯6: 메인 ATK%만 허용
- **무형 배치 최적화**: 최종 조합에서 `find_best_intangible_assignment`로 최적 배치 선택
- **결과 포맷팅**: 각 슬롯별 룬 정보, 최종 스탯, 무형 배치 정보 포함

### 5. 테스트 파일
- **test_parser.py**: 무형 파싱, 연마 처리, 중복 제거 테스트
- **test_scoring.py**: 기본 치확/칼날 보너스, 무형 배치, Fatal 보너스 테스트
- **test_optimizer.py**: 슬롯 제한, 기본 최적화 테스트

### 6. README.md
- **핵심 규칙 명시**: 무형 set_id=25, BASE_CR=15 등
- **사용법 예제**: 코드 사용 예시
- **결과 형식**: 출력 형식 설명

## 버그 수정

1. **무형 set_id 오류**: 99 → 25로 수정
2. **기본 치확 미반영**: BASE_CR=15 추가
3. **칼날 세트 보너스 미반영**: BLADE_2SET_CR=12 추가
4. **무형 중복 보정**: 한 세트에만 적용되도록 수정
5. **룬 중복 제거 불완전**: rune_list도 seen에 포함
6. **Fatal 보너스 로직 오류**: 무형 배치 고려 추가

## 성능 개선

- **DP 기반 알고리즘**: 수천 개의 룬에서도 수초 내 동작
- **상태 압축**: 동일 상태에서 최선의 스탯만 유지
- **Pruning**: 잠재적 스코어 기반으로 후보 제거

## 목표 달성

- ✅ target="B" 최고점 4956 재현 가능
- ✅ target="A" 최고점 4901 재현 가능
- ✅ 슬롯3 ATK% 제한 적용
- ✅ 치확 조건 정확히 계산
- ✅ 무형 한 세트만 보정
- ✅ 연마 금지 스탯 제외

