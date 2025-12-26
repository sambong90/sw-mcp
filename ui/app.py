"""Minimal Streamlit UI for rune optimizer"""

import streamlit as st
import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sw_core.api import run_search, run_search_from_json
from sw_core.swex_parser import parse_swex_json
from sw_core.monster_registry import get_registry


st.set_page_config(page_title="SW-MCP Rune Optimizer", layout="wide")

st.title("SW-MCP: Summoners War Rune Optimizer")
st.markdown("범용 룬 빌드 최적화 엔진 (모든 몬스터, 모든 세트 지원)")

# Sidebar: Configuration
with st.sidebar:
    st.header("설정")
    
    # Mode selection
    mode = st.selectbox("모드", ["exhaustive", "fast"], index=0)
    if mode == "fast":
        st.warning("⚠️ Fast 모드: 정확도 보장 없음 (heuristic pruning 사용)")
    else:
        st.info("✅ Exhaustive 모드: 정확도 100% 보장 (누락 없음)")
    
    # Monster selection
    monster_option = st.radio("몬스터 선택", ["자동 (레지스트리)", "수동 입력"])
    
    if monster_option == "수동 입력":
        base_atk = st.number_input("Base ATK", min_value=1, value=900)
        base_spd = st.number_input("Base SPD", min_value=1, value=104)
        base_hp = st.number_input("Base HP", min_value=1, value=10000)
        base_def = st.number_input("Base DEF", min_value=1, value=500)
        monster = None
    else:
        monster_name = st.text_input("몬스터 이름 (예: Lushen)", value="Lushen")
        monster = {"name": monster_name} if monster_name else None
        base_atk = base_spd = base_hp = base_def = None
    
    # Constraints
    st.subheader("제약 조건")
    constraint_spd = st.number_input("최소 SPD", min_value=0, value=0)
    constraint_cr = st.number_input("최소 CR", min_value=0, value=0, max_value=100)
    constraint_cd = st.number_input("최소 CD", min_value=0, value=0)
    constraint_atk_total = st.number_input("최소 ATK_TOTAL", min_value=0, value=0)
    
    constraints = {}
    if constraint_spd > 0:
        constraints["SPD"] = constraint_spd
    if constraint_cr > 0:
        constraints["CR"] = constraint_cr
    if constraint_cd > 0:
        constraints["CD"] = constraint_cd
    if constraint_atk_total > 0:
        constraints["ATK_TOTAL"] = constraint_atk_total
    
    # Set constraints
    st.subheader("세트 제약 (선택)")
    require_sets = st.checkbox("세트 조건 필수", value=False)
    set_rage = st.number_input("Rage (4-set)", min_value=0, max_value=4, value=0)
    set_fatal = st.number_input("Fatal (4-set)", min_value=0, max_value=4, value=0)
    set_blade = st.number_input("Blade (2-set)", min_value=0, max_value=2, value=0)
    
    set_constraints = {}
    if require_sets:
        if set_rage > 0:
            set_constraints["Rage"] = set_rage
        if set_fatal > 0:
            set_constraints["Fatal"] = set_fatal
        if set_blade > 0:
            set_constraints["Blade"] = set_blade
    
    # Objective
    objective = st.selectbox(
        "목표 함수",
        ["SCORE", "ATK_TOTAL", "ATK_BONUS", "SPD", "CD", "EHP", "DAMAGE_PROXY"],
        index=0
    )
    
    # Top N
    top_n = st.number_input("상위 N개", min_value=1, max_value=100, value=20)
    
    # Return all
    return_all = st.checkbox("모든 결과 반환 (메모리 주의)", value=False)

# Main area: File upload and results
tab1, tab2 = st.tabs(["SWEX JSON 업로드", "결과"])

with tab1:
    st.subheader("SWEX JSON 파일 업로드")
    uploaded_file = st.file_uploader("SWEX JSON 파일 선택", type=["json"])
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"파일 로드 성공: {len(json_data.get('runes', []))} 룬")
            
            # Parse runes
            runes = parse_swex_json(json_data)
            st.info(f"파싱된 룬 수: {len(runes)}")
            
            # Store in session state
            st.session_state['runes'] = runes
            st.session_state['json_data'] = json_data
            
        except Exception as e:
            st.error(f"파일 파싱 오류: {e}")

with tab2:
    if 'runes' not in st.session_state:
        st.warning("먼저 SWEX JSON 파일을 업로드하세요.")
    else:
        runes = st.session_state['runes']
        
        if st.button("탐색 실행", type="primary"):
            with st.spinner("탐색 중..."):
                try:
                    result = run_search(
                        runes,
                        monster=monster,
                        base_atk=base_atk,
                        base_spd=base_spd,
                        base_hp=base_hp,
                        base_def=base_def,
                        constraints=constraints,
                        set_constraints=set_constraints if set_constraints else None,
                        objective=objective,
                        top_n=top_n,
                        return_all=return_all,
                        mode=mode
                    )
                    
                    st.success(f"탐색 완료: {len(result.get('results', []))}개 빌드 발견")
                    
                    # Display results
                    results = result.get('results', [])
                    if results:
                        st.subheader(f"상위 {len(results)}개 빌드")
                        
                        # Results table
                        import pandas as pd
                        
                        table_data = []
                        for i, r in enumerate(results, 1):
                            table_data.append({
                                "순위": i,
                                "Score": r.get("score", 0),
                                "CR": f"{r.get('cr_total', 0):.1f}",
                                "CD": f"{r.get('cd_total', 0):.1f}",
                                "ATK_TOTAL": r.get("atk_total", 0),
                                "SPD": f"{r.get('spd_total', 0):.1f}",
                                "HP_TOTAL": r.get("hp_total", 0),
                                "DEF_TOTAL": r.get("def_total", 0),
                            })
                        
                        df = pd.DataFrame(table_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # Detailed view
                        st.subheader("상세 정보")
                        selected_idx = st.selectbox("빌드 선택", range(len(results)), format_func=lambda x: f"빌드 #{x+1} (Score: {results[x].get('score', 0)})")
                        
                        selected = results[selected_idx]
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**스탯**")
                            st.json({
                                "Score": selected.get("score", 0),
                                "CR": selected.get("cr_total", 0),
                                "CD": selected.get("cd_total", 0),
                                "ATK_TOTAL": selected.get("atk_total", 0),
                                "ATK_BONUS": selected.get("atk_bonus", 0),
                                "SPD": selected.get("spd_total", 0),
                                "HP_TOTAL": selected.get("hp_total", 0),
                                "DEF_TOTAL": selected.get("def_total", 0),
                            })
                        
                        with col2:
                            st.write("**슬롯별 룬**")
                            slots = selected.get("slots", {})
                            for slot in range(1, 7):
                                if slot in slots:
                                    slot_info = slots[slot]
                                    st.write(f"**Slot {slot}:**")
                                    st.write(f"  - Set: {slot_info.get('set_name', '?')}")
                                    st.write(f"  - Main: {slot_info.get('main', '?')}")
                                    if slot_info.get('prefix'):
                                        st.write(f"  - Prefix: {slot_info.get('prefix', '?')}")
                                    if slot_info.get('subs'):
                                        st.write(f"  - Subs: {', '.join(slot_info.get('subs', []))}")
                        
                        # Export
                        st.subheader("내보내기")
                        if st.button("CSV로 내보내기"):
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="CSV 다운로드",
                                data=csv,
                                file_name="rune_builds.csv",
                                mime="text/csv"
                            )
                    else:
                        st.warning("조건을 만족하는 빌드가 없습니다.")
                        
                except Exception as e:
                    st.error(f"탐색 오류: {e}")
                    import traceback
                    st.code(traceback.format_exc())
