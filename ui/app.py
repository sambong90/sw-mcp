"""Minimal Streamlit UI for rune optimizer"""

import streamlit as st
import json
import sys
from pathlib import Path

# Add src to path
# Get absolute path to project root
import os
app_file = Path(__file__).resolve()
# Find project root by looking for src/sw_core directory
current = app_file.parent
src_path = None
while current != current.parent:  # Stop at filesystem root
    src_core = current / "src" / "sw_core"
    if src_core.exists() and (src_core / "__init__.py").exists():
        src_path = current / "src"
        break
    current = current.parent

if src_path is None:
    # Fallback: use parent.parent (should work if running from project root)
    src_path = app_file.parent.parent / "src"

# Add to path if it exists and not already in path
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
elif not src_path.exists():
    # Error: cannot find src directory
    st.error(f"❌ Cannot find src directory. Expected at: {src_path}")
    st.stop()

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
        # 몬스터 레지스트리 초기화
        if 'monster_registry' not in st.session_state:
            registry = get_registry(data_dirs=["data"])
            registry.warm_cache()  # 모든 몬스터 미리 로드
            st.session_state['monster_registry'] = registry
        else:
            registry = st.session_state['monster_registry']
        
        # 모든 몬스터 목록 생성 (한 번만)
        if 'monster_options' not in st.session_state:
            monster_options = ["선택 안 함"]
            monster_dict = {}
            
            for master_id, stats in registry._cache.items():
                display_name = stats.name_ko if stats.name_ko else stats.name_en
                if stats.name_ko and stats.name_en:
                    display_name = f"{stats.name_ko} ({stats.name_en})"
                
                option_text = f"{display_name} (ID: {stats.master_id})"
                monster_options.append(option_text)
                monster_dict[option_text] = stats
            
            # 이름 순으로 정렬
            monster_options = [monster_options[0]] + sorted(monster_options[1:])
            st.session_state['monster_options'] = monster_options
            st.session_state['monster_dict'] = monster_dict
        
        monster_options = st.session_state['monster_options']
        monster_dict = st.session_state['monster_dict']
        
        # 통합된 선택 박스 (드롭다운에서 직접 검색 가능)
        selected_option = st.selectbox(
            "몬스터 선택",
            monster_options,
            key="monster_select",
            help="드롭다운을 열어서 직접 검색할 수 있습니다. 한 글자만 입력해도 필터링됩니다."
        )
        
        # 선택된 몬스터 정보
        monster = None
        base_atk = base_spd = base_hp = base_def = None
        
        if selected_option != "선택 안 함":
            selected_stats = monster_dict[selected_option]
            monster = {"master_id": selected_stats.master_id, "name": selected_stats.name_ko or selected_stats.name_en}
            base_atk = selected_stats.base_atk
            base_spd = selected_stats.base_spd
            base_hp = selected_stats.base_hp
            base_def = selected_stats.base_def
            
            # 선택된 몬스터 정보 표시
            st.success(f"✓ 선택: {selected_stats.name_ko or selected_stats.name_en} | "
                      f"ATK: {base_atk}, SPD: {base_spd}, HP: {base_hp}, DEF: {base_def}")
        else:
            st.info("💡 드롭다운을 열어서 몬스터 이름을 입력하면 자동으로 필터링됩니다 (예: '루', 'Lushen', '베라' 등)")
    
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
