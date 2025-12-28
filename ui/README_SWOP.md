# SWOP 스타일 대시보드 UI

## 개요

SWOP(Summoners War Optimizer) 스타일의 대시보드 UI로 리디자인된 Streamlit 기반 인터페이스입니다.

## 실행 방법

```bash
# Plan A: Streamlit 버전
streamlit run ui/app_swop.py --server.port 8501

# 기존 UI (참고용)
streamlit run ui/app.py --server.port 8502
```

## 주요 기능

### 레이아웃
- **상단 헤더**: 프로젝트명 + 세션 제어 + 파일 업로드
- **3열 그리드**:
  - 좌측: PICK A MONSTER (몬스터 선택 + 기본 스탯)
  - 중앙: SETS (세트 제약 설정)
  - 우측: OPTIONS (모드/목표/고급 옵션)
- **중단 패널**: FILTERS, ARTIFACTS, FOCUS
- **하단**: OPTIMIZE 버튼 + 결과 테이블

### 다크 테마
- 배경: #1e1e1e
- 패널: #2d2d2d
- 강조색: #ff6b35 (주황/골드 톤)

### 기능
- ✅ SWEX JSON 업로드 (드래그&드롭)
- ✅ 몬스터 선택 (레지스트리/수동)
- ✅ 세트 제약 (Rage/Fatal/Blade)
- ✅ 필터 (최소 SPD/CR/CD/ATK_TOTAL)
- ✅ 목표 함수 선택
- ✅ 결과 테이블 + CSV Export
- ✅ 상세 정보 보기

## 한계 평가

### Streamlit 제약사항
1. **고정 레이아웃**: 하단 테이블이 스크롤 영역에 포함됨 (완전 고정 어려움)
2. **대량 데이터**: `st.dataframe`은 1000+ 행에서 성능 저하 가능
3. **상호작용**: 행 선택→상세 드로어 같은 복잡한 UX 제한적
4. **다크 테마**: CSS로 구현했으나 Streamlit 기본 스타일과 충돌 가능

### 전환 조건 체크
- [ ] 패널 배치/고정 영역: ⚠️ 부분적 (CSS로 해결 가능하나 완벽하지 않음)
- [ ] 대량 행 성능: ⚠️ 1000+ 행에서 제한적
- [ ] 상호작용 복잡도: ⚠️ 기본 기능은 가능하나 고급 UX 어려움
- [ ] 유지보수성: ✅ 현재 구조는 유지보수 가능

**결론**: Plan A로 기본 워크플로우는 구현 가능하나, 대량 데이터/고급 상호작용이 필요하면 Plan B 전환 권장

## Plan B (필요 시)

React + Vite + Tailwind + TanStack Table 기반 프론트엔드로 재구축:
- FastAPI 백엔드 API 분리
- 가상 스크롤 지원 테이블
- 완전한 다크 테마
- 고급 상호작용 (드로어/모달)


