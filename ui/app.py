"""Streamlit UI for SW-MCP"""

import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, Any, Optional
import time

# API base URL
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")


def upload_json_screen():
    """Screen 1: Upload SWEX JSON"""
    st.title("📤 SWEX JSON 업로드")
    
    uploaded_file = st.file_uploader(
        "SWEX JSON 파일을 선택하세요",
        type=["json"],
        help="서머너즈워 Exporter에서 내보낸 JSON 파일"
    )
    
    if uploaded_file is not None:
        try:
            # Read JSON
            json_data = json.load(uploaded_file)
            
            # Upload to API
            uploaded_file.seek(0)  # Reset file pointer
            files = {"file": (uploaded_file.name, uploaded_file, "application/json")}
            
            with st.spinner("업로드 중..."):
                response = requests.post(f"{API_BASE_URL}/imports", files=files)
            
            if response.status_code == 201:
                import_data = response.json()
                st.success(f"✅ 업로드 완료!")
                st.json(import_data)
                
                # Store import_id in session state
                st.session_state["import_id"] = import_data["id"]
                st.session_state["rune_count"] = import_data["rune_count"]
                
                if st.button("다음: 검색 설정"):
                    st.session_state["screen"] = "search_config"
                    st.rerun()
            else:
                st.error(f"업로드 실패: {response.text}")
        
        except json.JSONDecodeError:
            st.error("❌ 잘못된 JSON 파일입니다.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")


def search_config_screen():
    """Screen 2: Configure search"""
    st.title("⚙️ 검색 설정")
    
    if "import_id" not in st.session_state:
        st.warning("먼저 JSON 파일을 업로드하세요.")
        if st.button("업로드 화면으로"):
            st.session_state["screen"] = "upload"
            st.rerun()
        return
    
    st.info(f"Import ID: {st.session_state['import_id']} | 룬 개수: {st.session_state['rune_count']}")
    
    # Search parameters
    col1, col2 = st.columns(2)
    
    with col1:
        target = st.selectbox("Target", ["A", "B"], index=1, help="A: Rage+Blade, B: Fatal+Blade")
        mode = st.selectbox("Mode", ["exhaustive", "fast"], index=0, help="exhaustive: 완전 탐색, fast: 빠른 탐색")
        objective = st.selectbox(
            "Objective",
            ["SCORE", "ATK_TOTAL", "ATK_BONUS", "CD", "SPD"],
            index=0
        )
        top_n = st.number_input("Top N", min_value=1, max_value=1000, value=20)
    
    with col2:
        base_atk = st.number_input("Base ATK", min_value=1, value=900)
        base_spd = st.number_input("Base SPD", min_value=1, value=104)
        require_sets = st.checkbox("Require Sets", value=True, help="세트 조건 필수 여부")
        max_candidates = st.number_input("Max Candidates/Slot (fast mode)", min_value=1, value=300)
    
    # Constraints
    st.subheader("제약 조건 (선택사항)")
    constraints = {}
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cr_min = st.number_input("CR (최소)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
        if cr_min > 0:
            constraints["CR"] = cr_min
    
    with col2:
        spd_min = st.number_input("SPD (최소)", min_value=0.0, value=0.0, step=1.0)
        if spd_min > 0:
            constraints["SPD"] = spd_min
    
    with col3:
        atk_total_min = st.number_input("ATK_TOTAL (최소)", min_value=0.0, value=0.0, step=1.0)
        if atk_total_min > 0:
            constraints["ATK_TOTAL"] = atk_total_min
    
    with col4:
        min_score = st.number_input("MIN_SCORE", min_value=0.0, value=0.0, step=1.0)
        if min_score > 0:
            constraints["MIN_SCORE"] = min_score
    
    # Search button
    if st.button("🔍 검색 시작", type="primary"):
        # Create search job
        job_data = {
            "import_id": st.session_state["import_id"],
            "params": {
                "target": target,
                "mode": mode,
                "constraints": constraints if constraints else None,
                "objective": objective,
                "top_n": top_n,
                "return_policy": "top_n",
                "base_atk": base_atk,
                "base_spd": base_spd,
                "require_sets": require_sets,
                "max_candidates_per_slot": max_candidates,
                "max_results": 2000
            }
        }
        
        with st.spinner("검색 작업 생성 중..."):
            response = requests.post(f"{API_BASE_URL}/search-jobs", json=job_data)
        
        if response.status_code == 201:
            job_data = response.json()
            st.session_state["job_id"] = job_data["id"]
            st.session_state["screen"] = "results"
            st.rerun()
        else:
            st.error(f"검색 작업 생성 실패: {response.text}")


def results_screen():
    """Screen 3: Job progress and results"""
    st.title("📊 검색 결과")
    
    if "job_id" not in st.session_state:
        st.warning("검색 작업이 없습니다.")
        if st.button("검색 설정으로"):
            st.session_state["screen"] = "search_config"
            st.rerun()
        return
    
    job_id = st.session_state["job_id"]
    
    # Poll job status
    with st.spinner("작업 상태 확인 중..."):
        response = requests.get(f"{API_BASE_URL}/search-jobs/{job_id}")
    
    if response.status_code != 200:
        st.error(f"작업 조회 실패: {response.text}")
        return
    
    job = response.json()
    status = job["status"]
    progress = job.get("progress", 0.0)
    
    # Status display
    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫"
    }
    
    st.subheader(f"{status_emoji.get(status, '❓')} 상태: {status.upper()}")
    
    if status == "running":
        st.progress(progress)
        st.caption(f"진행률: {progress * 100:.1f}%")
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()
    
    elif status == "pending":
        st.info("작업이 대기 중입니다. 잠시 후 자동으로 새로고침됩니다.")
        time.sleep(2)
        st.rerun()
    
    elif status == "failed":
        st.error(f"작업 실패: {job.get('error_message', 'Unknown error')}")
        if st.button("다시 시도"):
            st.session_state["screen"] = "search_config"
            st.rerun()
    
    elif status == "cancelled":
        st.warning("작업이 취소되었습니다.")
        if st.button("새 검색"):
            st.session_state["screen"] = "search_config"
            st.rerun()
    
    elif status == "completed":
        # Get results
        with st.spinner("결과 로딩 중..."):
            results_response = requests.get(f"{API_BASE_URL}/search-jobs/{job_id}/results")
        
        if results_response.status_code == 200:
            results_data = results_response.json()
            total_found = results_data["total_found"]
            results = results_data["results"]
            
            st.success(f"✅ {total_found}개의 빌드를 찾았습니다!")
            
            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 JSON로 내보내기"):
                    st.download_button(
                        label="다운로드",
                        data=json.dumps(results_data, indent=2, ensure_ascii=False),
                        file_name=f"search_results_{job_id}.json",
                        mime="application/json"
                    )
            
            with col2:
                # CSV export
                if results:
                    df = pd.DataFrame([
                        {
                            "Rank": r["rank"],
                            "Score": r["score"],
                            "CR": r["stats_json"].get("cr_total", 0),
                            "CD": r["stats_json"].get("cd_total", 0),
                            "ATK_TOTAL": r["stats_json"].get("atk_total", 0),
                            "SPD": r["stats_json"].get("spd_total", 0),
                        }
                        for r in results
                    ])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📊 CSV로 내보내기",
                        data=csv,
                        file_name=f"search_results_{job_id}.csv",
                        mime="text/csv"
                    )
            
            # Results table
            if results:
                st.subheader("결과 테이블")
                
                # Create DataFrame for display
                display_data = []
                for r in results:
                    stats = r["stats_json"]
                    display_data.append({
                        "Rank": r["rank"],
                        "Score": f"{r['score']:.1f}",
                        "CR": f"{stats.get('cr_total', 0):.1f}%",
                        "CD": f"{stats.get('cd_total', 0):.1f}%",
                        "ATK%": f"{stats.get('atk_pct_total', 0):.1f}%",
                        "ATK_TOTAL": int(stats.get("atk_total", 0)),
                        "SPD": int(stats.get("spd_total", 0)),
                    })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
                
                # Build detail view
                st.subheader("빌드 상세")
                selected_rank = st.selectbox(
                    "랭크 선택",
                    options=[r["rank"] for r in results],
                    index=0
                )
                
                selected_build = next(r for r in results if r["rank"] == selected_rank)
                build_json = selected_build["build_json"]
                
                # Display build details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**스탯 요약**")
                    stats = selected_build["stats_json"]
                    st.json({
                        "Score": stats.get("score", 0),
                        "CR": f"{stats.get('cr_total', 0):.1f}%",
                        "CD": f"{stats.get('cd_total', 0):.1f}%",
                        "ATK%": f"{stats.get('atk_pct_total', 0):.1f}%",
                        "ATK_TOTAL": stats.get("atk_total", 0),
                        "SPD": stats.get("spd_total", 0),
                    })
                
                with col2:
                    st.write("**세트 정보**")
                    if "intangible_assignment" in build_json:
                        st.write(f"무형 배치: {build_json['intangible_assignment']}")
                    if "slots" in build_json:
                        st.write(f"슬롯 수: {len(build_json['slots'])}")
                
                # Slot details
                if "slots" in build_json:
                    st.write("**슬롯별 룬**")
                    for slot_num in sorted(build_json["slots"].keys(), key=int):
                        slot_data = build_json["slots"][slot_num]
                        with st.expander(f"슬롯 {slot_num}"):
                            st.json(slot_data)
        else:
            st.error(f"결과 조회 실패: {results_response.text}")


def main():
    """Main app"""
    # Initialize session state
    if "screen" not in st.session_state:
        st.session_state["screen"] = "upload"
    
    # Sidebar navigation
    with st.sidebar:
        st.title("SW-MCP")
        st.write("서머너즈워 룬 최적화")
        
        if st.button("🏠 홈 (업로드)"):
            st.session_state["screen"] = "upload"
            st.rerun()
        
        if st.button("⚙️ 검색 설정"):
            if "import_id" in st.session_state:
                st.session_state["screen"] = "search_config"
                st.rerun()
            else:
                st.warning("먼저 JSON을 업로드하세요.")
    
    # Route to screen
    if st.session_state["screen"] == "upload":
        upload_json_screen()
    elif st.session_state["screen"] == "search_config":
        search_config_screen()
    elif st.session_state["screen"] == "results":
        results_screen()


if __name__ == "__main__":
    main()

