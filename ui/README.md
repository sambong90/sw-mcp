# SW-MCP UI

Streamlit 기반 웹 UI입니다.

## 실행 방법

```bash
# Streamlit 설치
pip install streamlit requests pandas

# UI 실행
cd ui
streamlit run app.py
```

## 환경 변수

`.streamlit/secrets.toml` 파일을 생성하여 API URL을 설정할 수 있습니다:

```toml
API_BASE_URL = "http://localhost:8000"
```

## 기능

1. **JSON 업로드**: SWEX JSON 파일 업로드
2. **검색 설정**: Target, Mode, Constraints, Objective 설정
3. **결과 보기**: Job progress, Results table, Build detail view
4. **내보내기**: JSON/CSV 형식으로 결과 다운로드

