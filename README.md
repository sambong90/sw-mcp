# SW MCP - 서머너즈워 룬 최적화

서머너즈워 SWOP 수준의 정확도로 루쉔 최적화를 수행하는 Python 라이브러리입니다.

## 주요 기능

- SWEX JSON 형식의 룬 데이터 파싱
- 루쉔 최적화 (격노+칼날, 맹공+칼날)
- DP 기반 효율적인 최적화 알고리즘
- 무형(Intangible) 룬 배치 최적화

## 핵심 규칙

### 세트 ID
- **무형(Intangible) 세트**: `set_id = 25` (JSON에서 실제 값)
- 기타 세트는 표준 SWEX 형식 사용

### 기본 스탯
- **기본 치명타 확률(CR)**: 15%
- **기본 치명타 데미지(CD)**: 50%

### 세트 보너스
- **Rage 4세트**: 치명타 데미지 +40%
- **Fatal 4세트**: 공격력 +35%
- **Blade 2세트**: 치명타 확률 +12%

### 치확 조건
치확 조건은 다음 공식으로 계산됩니다:
```
총 치확 = 기본 치확(15) + 칼날 세트 보너스(12) + 룬 치확
총 치확 >= 100% 이어야 함
```

### 무형 룬 배치
- 무형 룬은 **한 세트에만** 보정할 수 있습니다
- 무형 1개가 Rage/Fatal과 Blade에 동시에 기여할 수 없습니다
- 최적화 시 다음 옵션을 평가합니다:
  - `to_Rage` / `to_Fatal`: Rage/Fatal 세트 카운트에 +1
  - `to_Blade`: Blade 세트 카운트에 +1
  - `none`: 무형 없이 계산

### 슬롯 제한
- **슬롯 2**: 메인 스탯 ATK%만 허용
- **슬롯 3**: 서브옵에 ATK% 금지 (ATK+도 금지)
- **슬롯 4**: 메인 스탯 CD만 허용
- **슬롯 6**: 메인 스탯 ATK%만 허용

### 연마 금지 스탯
연마 시뮬레이션에 포함하지 않는 스탯:
- CR (치명타 확률)
- CD (치명타 데미지)
- ACC (명중)
- RES (저항)

## 사용법

```python
from src.sw_mcp.swex_parser import load_swex_json
from src.sw_mcp.optimizer import optimize_lushen

# SWEX JSON 로드
runes = load_swex_json("swex_export.json")

# 루쉔 최적화 (맹공+칼날)
results = optimize_lushen(
    runes=runes,
    target="B",  # "A" (격노+칼날) 또는 "B" (맹공+칼날)
    gem_mode="none",
    grind_mode="none",
    top_n=10
)

# 결과 출력
for i, result in enumerate(results, 1):
    print(f"#{i} Score: {result['score']:.2f}")
    print(f"  CR: {result['cr_total']:.1f}%")
    print(f"  CD: {result['cd_total']:.1f}%")
    print(f"  ATK%: {result['atk_pct_total']:.1f}%")
    print(f"  ATK+: {result['atk_flat_total']:.0f}")
    print(f"  무형 배치: {result['intangible_assignment']}")
    print()
```

## 결과 형식

```python
{
    "score": 4956.0,
    "cr_total": 100.0,
    "cd_total": 200.0,
    "atk_pct_total": 350.0,
    "atk_flat_total": 100.0,
    "atk_bonus": 360.0,
    "intangible_assignment": "to_Fatal",
    "slots": {
        1: {
            "rune_id": 12345,
            "set": "Fatal",
            "main": "ATK% 63",
            "subs": ["CR 20", "CD 7"]
        },
        # ... 슬롯 2~6
    }
}
```

## 목표 점수

- **target="B" (맹공+칼날)**: 최고점 4956 (무형 1개 포함 케이스)
- **target="A" (격노+칼날)**: 최고점 4901

## 프로젝트 구조

```
sw-mcp/
├── src/
│   └── sw_mcp/
│       ├── __init__.py
│       ├── types.py          # 타입 정의 및 상수
│       ├── swex_parser.py    # SWEX JSON 파서
│       ├── scoring.py        # 빌드 스코어링
│       └── optimizer.py      # 최적화 알고리즘
├── tests/
│   ├── test_parser.py
│   ├── test_scoring.py
│   └── test_optimizer.py
└── README.md
```

## 개발 노트

### 주요 수정 사항
1. 무형 세트 ID를 99에서 25로 수정
2. 기본 치확 15와 칼날 세트 보너스 12 적용
3. 무형 룬 배치 로직 개선 (한 세트에만 적용)
4. 룬 중복 제거 로직 개선 (rune_list + unit_list 병합)
5. DP 기반 최적화 알고리즘으로 성능 개선

### 성능
- 수천 개의 룬에서도 수초 내 동작
- DP 기반으로 정확도와 성능을 동시에 만족

## 라이선스

MIT License

