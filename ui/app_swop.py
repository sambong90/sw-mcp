"""SWOP-style Dashboard UI for SW-MCP Rune Optimizer"""

import streamlit as st
import json
import sys
import pandas as pd
from pathlib import Path

# Add src to path
import os
app_file = Path(__file__).resolve()
current = app_file.parent
src_path = None
while current != current.parent:
    src_core = current / "src" / "sw_core"
    if src_core.exists() and (src_core / "__init__.py").exists():
        src_path = current / "src"
        break
    current = current.parent

if src_path is None:
    src_path = app_file.parent.parent / "src"

if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
elif not src_path.exists():
    st.error(f"❌ Cannot find src directory. Expected at: {src_path}")
    st.stop()

from sw_core.api import run_search
from sw_core.swex_parser import parse_swex_json
from sw_core.monster_registry import get_registry
from sw_core.types import SET_ID_NAME, STAT_ID_NAME
from sw_core.rules import slot_main_is_allowed
from sw_core.set_meta import (
    get_set_requirement, generate_set_combinations, 
    is_valid_combination, get_required_count
)


# Page config
st.set_page_config(
    page_title="SW-MCP Optimizer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for light theme with SWOP-style layout
st.markdown("""
<style>
    /* Light theme base */
    .stApp {
        background-color: #f5f5f5;
        color: #1a1a1a;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        padding: 1.5rem 2rem;
        border-bottom: 3px solid #ff6b35;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: #ff6b35;
        margin: 0;
        font-size: 1.8rem;
        font-weight: bold;
    }
    
    .main-header p {
        color: #555555;
        margin: 0.5rem 0 0 0;
    }
    
    /* Panel styling */
    .panel {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    
    .panel-title {
        color: #ff6b35;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.8rem;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 0.6rem;
    }
    
    /* Text colors */
    .stMarkdown, .stText {
        color: #1a1a1a;
    }
    
    .stMarkdown strong {
        color: #ff6b35;
    }
    
    /* Stats card */
    .stats-card {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.25rem 0;
    }
    
    .stats-label {
        color: #666666;
        font-size: 0.85rem;
    }
    
    .stats-value {
        color: #ff6b35;
        font-size: 1.1rem;
        font-weight: bold;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #ff6b35;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);
    }
    
    .stButton>button:hover {
        background-color: #ff8c5a;
        box-shadow: 0 4px 8px rgba(255, 107, 53, 0.4);
        transform: translateY(-1px);
    }
    
    /* Results table styling */
    .results-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-top: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    
    /* Input styling */
    .stNumberInput>div>div>input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 4px;
    }
    
    .stNumberInput>div>div>input:focus {
        border-color: #ff6b35 !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.2);
    }
    
    .stSelectbox>div>div {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #d0d0d0 !important;
    }
    
    .stSelectbox>div>div:focus-within {
        border-color: #ff6b35 !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.2);
    }
    
    .stTextInput>div>div>input {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #d0d0d0 !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #ff6b35 !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.2);
    }
    
    /* Checkbox and radio styling */
    .stCheckbox>label, .stRadio>label {
        color: #1a1a1a;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #ff6b35;
    }
    
    [data-testid="stMetricLabel"] {
        color: #666666;
    }
    
    /* Dataframe styling */
    .dataframe {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    
    .dataframe thead {
        background-color: #f5f5f5;
        color: #ff6b35;
        font-weight: bold;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: #fafafa;
    }
    
    .dataframe tbody tr:hover {
        background-color: #f0f0f0;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        color: #1a1a1a;
        border: 1px solid #e0e0e0;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #fafafa;
    }
    
    /* Caption styling */
    .stCaption {
        color: #666666;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f5f5f5;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d0d0d0;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #b0b0b0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'runes' not in st.session_state:
    st.session_state['runes'] = None
if 'json_data' not in st.session_state:
    st.session_state['json_data'] = None
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None
if 'monster_registry' not in st.session_state:
    registry = get_registry(data_dirs=["data"])
    registry.warm_cache()
    st.session_state['monster_registry'] = registry
    # Pre-build monster options
    monster_options = ["선택 안 함"]
    monster_dict = {}
    for master_id, stats in registry._cache.items():
        display_name = stats.name_ko if stats.name_ko else stats.name_en
        if stats.name_ko and stats.name_en:
            display_name = f"{stats.name_ko} ({stats.name_en})"
        option_text = f"{display_name} (ID: {stats.master_id})"
        monster_options.append(option_text)
        monster_dict[option_text] = stats
    monster_options = [monster_options[0]] + sorted(monster_options[1:])
    st.session_state['monster_options'] = monster_options
    st.session_state['monster_dict'] = monster_dict


# Header
st.markdown("""
<div class="main-header">
    <h1>⚔️ SW-MCP Rune Optimizer</h1>
    <p style="color: #999; margin: 0.5rem 0 0 0;">범용 룬 빌드 최적화 엔진</p>
</div>
""", unsafe_allow_html=True)

# Top bar: Session control + File upload
col_header1, col_header2, col_header3 = st.columns([2, 1, 1])

with col_header1:
    uploaded_file = st.file_uploader(
        "📁 SWEX JSON 업로드",
        type=["json"],
        key="file_upload",
        help="SWEX JSON 파일을 드래그&드롭하거나 선택하세요"
    )
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            runes = parse_swex_json(json_data)
            st.session_state['runes'] = runes
            st.session_state['json_data'] = json_data
            st.success(f"✅ {len(runes)}개 룬 로드됨")
        except Exception as e:
            st.error(f"❌ 파일 파싱 오류: {e}")

with col_header2:
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state['runes'] = None
        st.session_state['search_results'] = None
        st.rerun()

with col_header3:
    if st.session_state.get('runes'):
        st.metric("로드된 룬", len(st.session_state['runes']))
    else:
        st.info("파일 업로드 필요")


# Main 3-column layout
col1, col2, col3 = st.columns([1.2, 1.5, 1.3])

# ===== LEFT COLUMN: PICK A MONSTER =====
with col1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">PICK A MONSTER</div>', unsafe_allow_html=True)
    
    # Monster selection mode
    monster_mode = st.radio(
        "선택 방식",
        ["자동 (레지스트리)", "수동 입력"],
        horizontal=True,
        key="monster_mode"
    )
    
    monster = None
    base_atk = base_spd = base_hp = base_def = None
    
    if monster_mode == "자동 (레지스트리)":
        registry = st.session_state['monster_registry']
        monster_options = st.session_state['monster_options']
        monster_dict = st.session_state['monster_dict']
        
        selected_option = st.selectbox(
            "몬스터",
            monster_options,
            key="monster_select"
        )
        
        if selected_option != "선택 안 함":
            selected_stats = monster_dict[selected_option]
            monster = {
                "master_id": selected_stats.master_id,
                "name": selected_stats.name_ko or selected_stats.name_en
            }
            base_atk = selected_stats.base_atk
            base_spd = selected_stats.base_spd
            base_hp = selected_stats.base_hp
            base_def = selected_stats.base_def
            base_cr = selected_stats.base_cr
            base_cd = selected_stats.base_cd
            base_res = 15  # 기본값 (RES는 레지스트리에 없을 수 있음)
            base_acc = 0   # 기본값 (ACC는 레지스트리에 없을 수 있음)
            
            # Base/Actual 탭
            stat_tab1, stat_tab2 = st.tabs(["Base", "Actual"])
            
            with stat_tab1:
                st.markdown("### 기본 스탯")
                # 2열 그리드로 모든 스탯 표시
                stats_col1, stats_col2 = st.columns(2)
                with stats_col1:
                    st.metric("HP", f"{base_hp:,}")
                    st.metric("ATK", f"{base_atk:,}")
                    st.metric("DEF", f"{base_def:,}")
                    st.metric("SPD", base_spd)
                with stats_col2:
                    st.metric("CRIT", f"{base_cr}%")
                    st.metric("CDMG", f"{base_cd}%")
                    st.metric("RES", f"{base_res}%")
                    st.metric("ACC", f"{base_acc}%")
            
            with stat_tab2:
                st.info("🚧 Actual 스탯은 추후 구현 예정 (룬/아티팩트/리더 스킬 반영)")
    else:
        st.markdown("### 수동 입력")
        base_atk = st.number_input("Base ATK", min_value=1, value=900, key="base_atk")
        base_spd = st.number_input("Base SPD", min_value=1, value=104, key="base_spd")
        base_hp = st.number_input("Base HP", min_value=1, value=10000, key="base_hp")
        base_def = st.number_input("Base DEF", min_value=1, value=500, key="base_def")
    
    st.markdown('</div>', unsafe_allow_html=True)


# ===== MIDDLE COLUMN: SETS =====
with col2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">SETS</div>', unsafe_allow_html=True)
    
    # Initialize session state for sets (multi-select)
    if 'set1_selected' not in st.session_state:
        st.session_state['set1_selected'] = []
    if 'set2_selected' not in st.session_state:
        st.session_state['set2_selected'] = []
    if 'set3_selected' not in st.session_state:
        st.session_state['set3_selected'] = []
    if 'exclude_sets' not in st.session_state:
        st.session_state['exclude_sets'] = []
    if 'no_broken_sets' not in st.session_state:
        st.session_state['no_broken_sets'] = False
    
    # Get all set names (excluding Intangible and Unknown)
    all_sets = [name for sid, name in SET_ID_NAME.items() 
                if sid not in [25, 99] and name not in ["Intangible", "Unknown"]]
    all_sets.sort()
    
    # Exclude sets from options if they are in exclude list
    def get_available_sets():
        available = all_sets.copy()
        for excluded in st.session_state.get('exclude_sets', []):
            if excluded in available:
                available.remove(excluded)
        return available
    
    available_sets = get_available_sets()
    
    # SET 1, SET 2, SET 3 multi-select
    set_row1_col1, set_row1_col2 = st.columns([1, 3])
    with set_row1_col1:
        st.write("**SET 1**")
    with set_row1_col2:
        set1_selected = st.multiselect(
            "",
            available_sets,
            default=st.session_state.get('set1_selected', []),
            key="set1_multiselect",
            label_visibility="collapsed"
        )
        st.session_state['set1_selected'] = set1_selected
        # Display selected sets as chips
        if set1_selected:
            chips = " ".join([f"`{s}`" for s in set1_selected])
            st.markdown(f"선택: {chips}")
    
    set_row2_col1, set_row2_col2 = st.columns([1, 3])
    with set_row2_col1:
        st.write("**SET 2**")
    with set_row2_col2:
        set2_selected = st.multiselect(
            "",
            available_sets,
            default=st.session_state.get('set2_selected', []),
            key="set2_multiselect",
            label_visibility="collapsed"
        )
        st.session_state['set2_selected'] = set2_selected
        if set2_selected:
            chips = " ".join([f"`{s}`" for s in set2_selected])
            st.markdown(f"선택: {chips}")
    
    set_row3_col1, set_row3_col2 = st.columns([1, 3])
    with set_row3_col1:
        st.write("**SET 3**")
    with set_row3_col2:
        set3_selected = st.multiselect(
            "",
            available_sets,
            default=st.session_state.get('set3_selected', []),
            key="set3_multiselect",
            label_visibility="collapsed"
        )
        st.session_state['set3_selected'] = set3_selected
        if set3_selected:
            chips = " ".join([f"`{s}`" for s in set3_selected])
            st.markdown(f"선택: {chips}")
    
    st.markdown("---")
    
    # EXCLUDE section
    st.markdown("**EXCLUDE**")
    exclude_sets = st.multiselect(
        "제외할 세트",
        all_sets,
        default=st.session_state.get('exclude_sets', []),
        key="exclude_sets_select"
    )
    st.session_state['exclude_sets'] = exclude_sets
    
    # No broken sets toggle
    no_broken_sets = st.checkbox(
        "No broken sets",
        value=st.session_state.get('no_broken_sets', False),
        key="no_broken_sets_check"
    )
    st.session_state['no_broken_sets'] = no_broken_sets
    
    # Strict mode toggle (Allow other sets)
    if 'strict_sets' not in st.session_state:
        st.session_state['strict_sets'] = True
    
    # 그룹이 2개 이상 채워진 경우에만 Strict 모드 표시
    non_empty_groups = [g for g in [set1_selected, set2_selected, set3_selected] if g]
    if len(non_empty_groups) >= 2:
        strict_sets = st.checkbox(
            "Strict (선택된 세트만 사용)",
            value=st.session_state.get('strict_sets', True),
            key="strict_sets_check",
            help="ON: 선택된 세트로만 구성, OFF: 남는 슬롯은 자유"
        )
        st.session_state['strict_sets'] = strict_sets
    else:
        st.session_state['strict_sets'] = False  # 그룹이 1개만 있으면 자유
    
    # 조합 생성 및 표시
    set_groups = [set1_selected, set2_selected, set3_selected]
    combinations = generate_set_combinations(set_groups)
    
    if combinations:
        st.markdown("---")
        st.markdown(f"**검색 케이스: {len(combinations)}개**")
        combo_display = []
        for i, combo in enumerate(combinations[:5], 1):  # 최대 5개만 표시
            combo_str = " + ".join(combo)
            required = get_required_count(combo)
            combo_display.append(f"{i}. {combo_str} ({required}룬)")
        if len(combinations) > 5:
            combo_display.append(f"... 외 {len(combinations) - 5}개")
        st.caption("\n".join(combo_display))
    
    if st.button("Clear", key="clear_sets", use_container_width=True):
        st.session_state['set1_selected'] = []
        st.session_state['set2_selected'] = []
        st.session_state['set3_selected'] = []
        st.session_state['exclude_sets'] = []
        st.session_state['no_broken_sets'] = False
        st.session_state['strict_sets'] = True
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


# ===== RIGHT COLUMN: OPTIONS =====
with col3:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">OPTIONS</div>', unsafe_allow_html=True)
    
    # Mode
    mode = st.selectbox("Mode", ["exhaustive", "fast"], index=0, key="mode")
    if mode == "fast":
        st.caption("⚠️ 정확도 보장 없음")
    else:
        st.caption("✅ 정확도 100% 보장")
    
    # Objective
    objective = st.selectbox(
        "Objective",
        ["SCORE", "ATK_TOTAL", "ATK_BONUS", "SPD", "CD", "EHP", "DAMAGE_PROXY"],
        index=0,
        key="objective"
    )
    
    # Top N
    top_n = st.number_input("Top N", min_value=1, max_value=100, value=20, key="top_n")
    
    # Return all
    return_all = st.checkbox("모든 결과 반환 (메모리 주의)", value=False, key="return_all")
    
    # Advanced options (collapsible)
    with st.expander("고급 옵션"):
        st.checkbox("Use locked runes", value=False, key="use_locked")
        st.checkbox("Use only runes from inventory", value=True, key="inventory_only")
        st.checkbox("Max +12 for slots 1,3,5", value=True, key="max_12")
    
    st.markdown('</div>', unsafe_allow_html=True)


# ===== MIDDLE SECTION: SLOT MAIN STATS =====
st.markdown("---")

slot_main_col1, slot_main_col2, slot_main_col3 = st.columns(3)

# Initialize session state for slot main stats (multi-select)
if 'slot2_main_selected' not in st.session_state:
    st.session_state['slot2_main_selected'] = []
if 'slot4_main_selected' not in st.session_state:
    st.session_state['slot4_main_selected'] = []
if 'slot6_main_selected' not in st.session_state:
    st.session_state['slot6_main_selected'] = []

# Slot 2 main stat options (without "Any" for multiselect)
slot2_main_options = []
for stat_id, stat_name in STAT_ID_NAME.items():
    if slot_main_is_allowed(2, stat_id):
        slot2_main_options.append(stat_name)

# Slot 4 main stat options
slot4_main_options = []
for stat_id, stat_name in STAT_ID_NAME.items():
    if slot_main_is_allowed(4, stat_id):
        slot4_main_options.append(stat_name)

# Slot 6 main stat options
slot6_main_options = []
for stat_id, stat_name in STAT_ID_NAME.items():
    if slot_main_is_allowed(6, stat_id):
        slot6_main_options.append(stat_name)

with slot_main_col1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">SLOT 2</div>', unsafe_allow_html=True)
    slot2_main_selected = st.multiselect(
        "메인 스탯",
        slot2_main_options,
        default=st.session_state.get('slot2_main_selected', []),
        key="slot2_main_multiselect",
        help="여러 스탯 선택 가능 (비어있으면 제약 없음)"
    )
    st.session_state['slot2_main_selected'] = slot2_main_selected
    if slot2_main_selected:
        chips = " ".join([f"`{s}`" for s in slot2_main_selected])
        st.caption(f"선택: {chips}")
    else:
        st.caption("제약 없음")
    st.markdown('</div>', unsafe_allow_html=True)

with slot_main_col2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">SLOT 4</div>', unsafe_allow_html=True)
    slot4_main_selected = st.multiselect(
        "메인 스탯",
        slot4_main_options,
        default=st.session_state.get('slot4_main_selected', []),
        key="slot4_main_multiselect",
        help="여러 스탯 선택 가능 (비어있으면 제약 없음)"
    )
    st.session_state['slot4_main_selected'] = slot4_main_selected
    if slot4_main_selected:
        chips = " ".join([f"`{s}`" for s in slot4_main_selected])
        st.caption(f"선택: {chips}")
    else:
        st.caption("제약 없음")
    st.markdown('</div>', unsafe_allow_html=True)

with slot_main_col3:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">SLOT 6</div>', unsafe_allow_html=True)
    slot6_main_selected = st.multiselect(
        "메인 스탯",
        slot6_main_options,
        default=st.session_state.get('slot6_main_selected', []),
        key="slot6_main_multiselect",
        help="여러 스탯 선택 가능 (비어있으면 제약 없음)"
    )
    st.session_state['slot6_main_selected'] = slot6_main_selected
    if slot6_main_selected:
        chips = " ".join([f"`{s}`" for s in slot6_main_selected])
        st.caption(f"선택: {chips}")
    else:
        st.caption("제약 없음")
    st.markdown('</div>', unsafe_allow_html=True)


# ===== MIDDLE SECTION: FILTERS =====
st.markdown("---")

# Initialize filter state
if 'filters' not in st.session_state:
    st.session_state['filters'] = {
        'HP': {'min': None, 'max': None},
        'ATK': {'min': None, 'max': None},
        'DEF': {'min': None, 'max': None},
        'SPD': {'min': None, 'max': None},
        'CRIT': {'min': None, 'max': None},
        'CRITDMG': {'min': None, 'max': None},
        'ACC': {'min': None, 'max': None},
        'RES': {'min': None, 'max': None},
        'ATK_TOTAL': {'min': None, 'max': None},
        'ATK_BONUS': {'min': None, 'max': None},
        'HP_TOTAL': {'min': None, 'max': None},
        'DEF_TOTAL': {'min': None, 'max': None},
    }
if 'filters_applied' not in st.session_state:
    st.session_state['filters_applied'] = False

st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">FILTERS</div>', unsafe_allow_html=True)

# Filter buttons
filter_btn_col1, filter_btn_col2, filter_btn_col3, filter_btn_col4 = st.columns([1, 1, 1, 5])
with filter_btn_col1:
    apply_filters = st.button("Apply", key="filter_apply", use_container_width=True)
with filter_btn_col2:
    adapt_filters = st.button("Adapt", key="filter_adapt", use_container_width=True)
with filter_btn_col3:
    clear_filters = st.button("Clear", key="filter_clear", use_container_width=True)

if clear_filters:
    st.session_state['filters'] = {
        'HP': {'min': None, 'max': None},
        'ATK': {'min': None, 'max': None},
        'DEF': {'min': None, 'max': None},
        'SPD': {'min': None, 'max': None},
        'CRIT': {'min': None, 'max': None},
        'CRITDMG': {'min': None, 'max': None},
        'ACC': {'min': None, 'max': None},
        'RES': {'min': None, 'max': None},
        'ATK_TOTAL': {'min': None, 'max': None},
        'ATK_BONUS': {'min': None, 'max': None},
        'HP_TOTAL': {'min': None, 'max': None},
        'DEF_TOTAL': {'min': None, 'max': None},
    }
    st.session_state['filters_applied'] = False
    st.rerun()

if adapt_filters and st.session_state.get('search_results'):
    # Adapt filters from current results
    results = st.session_state['search_results'].get('results', [])
    if results:
        # Get min/max from current results
        stats_to_adapt = ['HP_TOTAL', 'ATK_TOTAL', 'DEF_TOTAL', 'SPD', 'CRIT', 'CRITDMG', 'ACC', 'RES']
        for stat in stats_to_adapt:
            values = []
            for r in results:
                if stat == 'HP_TOTAL':
                    values.append(r.get('hp_total', 0))
                elif stat == 'ATK_TOTAL':
                    values.append(r.get('atk_total', 0))
                elif stat == 'DEF_TOTAL':
                    values.append(r.get('def_total', 0))
                elif stat == 'SPD':
                    values.append(r.get('spd_total', 0))
                elif stat == 'CRIT':
                    values.append(r.get('cr_total', 0))
                elif stat == 'CRITDMG':
                    values.append(r.get('cd_total', 0))
                elif stat == 'ACC':
                    values.append(r.get('acc_total', 0))
                elif stat == 'RES':
                    values.append(r.get('res_total', 0))
            
            if values:
                st.session_state['filters'][stat] = {
                    'min': min(values),
                    'max': max(values)
                }
        st.rerun()

# Basic stats (2 columns)
st.markdown("**기본 스탯**")
filter_basic_col1, filter_basic_col2 = st.columns(2)

# Stat name mapping for display
stat_display_names = {
    'HP': 'HP',
    'ATK': 'ATK',
    'DEF': 'DEF',
    'SPD': 'SPD',
    'CRIT': 'CRIT',
    'CRITDMG': 'CRITDMG',
    'ACC': 'ACC',
    'RES': 'RES',
}

# Left column: HP, ATK, DEF, SPD
with filter_basic_col1:
    for stat in ['HP_TOTAL', 'ATK_TOTAL', 'DEF_TOTAL', 'SPD']:
        stat_display = stat_display_names.get(stat, stat)
        if stat == 'HP_TOTAL':
            stat_display = 'HP'
        elif stat == 'ATK_TOTAL':
            stat_display = 'ATK'
        elif stat == 'DEF_TOTAL':
            stat_display = 'DEF'
        
        filter_row_col1, filter_row_col2, filter_row_col3 = st.columns([2, 1, 2])
        with filter_row_col1:
            min_val = st.number_input(
                f"{stat_display} MIN",
                min_value=0,
                value=int(st.session_state['filters'][stat]['min']) if st.session_state['filters'][stat]['min'] is not None else 0,
                key=f"filter_{stat}_min",
                label_visibility="collapsed"
            )
            st.session_state['filters'][stat]['min'] = min_val if min_val > 0 else None
        with filter_row_col2:
            st.write(f"**{stat_display}**")
        with filter_row_col3:
            max_val = st.number_input(
                f"{stat_display} MAX",
                min_value=0,
                value=int(st.session_state['filters'][stat]['max']) if st.session_state['filters'][stat]['max'] is not None else 0,
                key=f"filter_{stat}_max",
                label_visibility="collapsed"
            )
            st.session_state['filters'][stat]['max'] = max_val if max_val > 0 else None

# Right column: CRIT, CRITDMG, ACC, RES
with filter_basic_col2:
    for stat in ['CRIT', 'CRITDMG', 'ACC', 'RES']:
        stat_display = stat_display_names.get(stat, stat)
        
        filter_row_col1, filter_row_col2, filter_row_col3 = st.columns([2, 1, 2])
        with filter_row_col1:
            min_val = st.number_input(
                f"{stat_display} MIN",
                min_value=0,
                value=int(st.session_state['filters'][stat]['min']) if st.session_state['filters'][stat]['min'] is not None else 0,
                key=f"filter_{stat}_min",
                label_visibility="collapsed"
            )
            st.session_state['filters'][stat]['min'] = min_val if min_val > 0 else None
        with filter_row_col2:
            st.write(f"**{stat_display}**")
        with filter_row_col3:
            max_val = st.number_input(
                f"{stat_display} MAX",
                min_value=0,
                value=int(st.session_state['filters'][stat]['max']) if st.session_state['filters'][stat]['max'] is not None else 0,
                key=f"filter_{stat}_max",
                label_visibility="collapsed"
            )
            st.session_state['filters'][stat]['max'] = max_val if max_val > 0 else None

# Advanced stats (expander)
with st.expander("고급 스탯 (Advanced)"):
    filter_adv_col1, filter_adv_col2 = st.columns(2)
    
    with filter_adv_col1:
        for stat in ['ATK_BONUS']:
            filter_row_col1, filter_row_col2, filter_row_col3 = st.columns([2, 1, 2])
            with filter_row_col1:
                min_val = st.number_input(
                    f"{stat} MIN",
                    min_value=0,
                    value=int(st.session_state['filters'][stat]['min']) if st.session_state['filters'][stat]['min'] is not None else 0,
                    key=f"filter_{stat}_min_adv",
                    label_visibility="collapsed"
                )
                st.session_state['filters'][stat]['min'] = min_val if min_val > 0 else None
            with filter_row_col2:
                st.write(f"**{stat}**")
            with filter_row_col3:
                max_val = st.number_input(
                    f"{stat} MAX",
                    min_value=0,
                    value=int(st.session_state['filters'][stat]['max']) if st.session_state['filters'][stat]['max'] is not None else 0,
                    key=f"filter_{stat}_max_adv",
                    label_visibility="collapsed"
                )
                st.session_state['filters'][stat]['max'] = max_val if max_val > 0 else None
    
    with filter_adv_col2:
        st.info("🚧 EHP, DMG, Efficiency 등은 Phase2에서 구현 예정")

# Validation: Check MIN > MAX
filter_errors = []
for stat, limits in st.session_state['filters'].items():
    if limits['min'] is not None and limits['max'] is not None:
        if limits['min'] > limits['max']:
            filter_errors.append(f"{stat}: MIN({limits['min']}) > MAX({limits['max']})")

if filter_errors:
    st.warning("⚠️ 필터 오류: " + ", ".join(filter_errors))

# Convert filters to constraints (for engine)
constraints = {}
for stat, limits in st.session_state['filters'].items():
    if limits['min'] is not None and limits['min'] > 0:
        # Map display names to engine names
        engine_stat = stat
        if stat == 'CRIT':
            engine_stat = 'CR'
        elif stat == 'CRITDMG':
            engine_stat = 'CD'
        elif stat == 'HP_TOTAL':
            engine_stat = 'HP_TOTAL'
        elif stat == 'ATK_TOTAL':
            engine_stat = 'ATK_TOTAL'
        elif stat == 'DEF_TOTAL':
            engine_stat = 'DEF_TOTAL'
        
        constraints[engine_stat] = limits['min']

if apply_filters:
    st.session_state['filters_applied'] = True
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ARTIFACTS and FOCUS panels (unchanged)
st.markdown("---")
other_col1, other_col2 = st.columns(2)

with other_col1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">ARTIFACTS</div>', unsafe_allow_html=True)
    st.info("🚧 추후 구현 예정")
    st.markdown('</div>', unsafe_allow_html=True)

with other_col2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">FOCUS</div>', unsafe_allow_html=True)
    st.info("🚧 추후 구현 예정")
    st.markdown('</div>', unsafe_allow_html=True)


# ===== OPTIMIZE BUTTON =====
st.markdown("---")

optimize_col1, optimize_col2, optimize_col3 = st.columns([2, 1, 1])

with optimize_col1:
    if st.session_state.get('runes') is None:
        st.warning("⚠️ 먼저 SWEX JSON 파일을 업로드하세요")
        optimize_disabled = True
    else:
        optimize_disabled = False

with optimize_col2:
    if st.session_state.get('runes'):
        estimated = len(st.session_state['runes']) ** 6  # Rough estimate
        if estimated > 1e12:
            st.metric("예상 빌드", f"{estimated/1e12:.1f}T")
        elif estimated > 1e9:
            st.metric("예상 빌드", f"{estimated/1e9:.1f}B")
        elif estimated > 1e6:
            st.metric("예상 빌드", f"{estimated/1e6:.1f}M")
        else:
            st.metric("예상 빌드", f"{estimated:.0f}")

with optimize_col3:
    if st.button("🚀 OPTIMIZE", type="primary", disabled=optimize_disabled, use_container_width=True):
        runes = st.session_state['runes']
        
        # Apply slot main stat filters (multi-select)
        filtered_runes = runes.copy()
        initial_count = len(filtered_runes)
        
        # Slot 2 filter (multi-select)
        slot2_selected = st.session_state.get('slot2_main_selected', [])
        if slot2_selected:
            stat_name_to_id = {v: k for k, v in STAT_ID_NAME.items()}
            target_stat_ids = [stat_name_to_id.get(name) for name in slot2_selected if stat_name_to_id.get(name)]
            if target_stat_ids:
                filtered_runes = [r for r in filtered_runes 
                                if r.slot != 2 or r.main_stat_id in target_stat_ids]
        
        # Slot 4 filter (multi-select)
        slot4_selected = st.session_state.get('slot4_main_selected', [])
        if slot4_selected:
            stat_name_to_id = {v: k for k, v in STAT_ID_NAME.items()}
            target_stat_ids = [stat_name_to_id.get(name) for name in slot4_selected if stat_name_to_id.get(name)]
            if target_stat_ids:
                filtered_runes = [r for r in filtered_runes 
                                if r.slot != 4 or r.main_stat_id in target_stat_ids]
        
        # Slot 6 filter (multi-select)
        slot6_selected = st.session_state.get('slot6_main_selected', [])
        if slot6_selected:
            stat_name_to_id = {v: k for k, v in STAT_ID_NAME.items()}
            target_stat_ids = [stat_name_to_id.get(name) for name in slot6_selected if stat_name_to_id.get(name)]
            if target_stat_ids:
                filtered_runes = [r for r in filtered_runes 
                                if r.slot != 6 or r.main_stat_id in target_stat_ids]
        
        # Debug info
        if len(filtered_runes) < initial_count:
            st.info(f"슬롯 메인 스탯 필터링: {initial_count} → {len(filtered_runes)} 룬")
        
        # Apply exclude sets filter
        exclude_sets = st.session_state.get('exclude_sets', [])
        if exclude_sets:
            set_name_to_id = {v: k for k, v in SET_ID_NAME.items()}
            exclude_set_ids = [set_name_to_id.get(name) for name in exclude_sets if set_name_to_id.get(name)]
            filtered_runes = [r for r in filtered_runes if r.set_id not in exclude_set_ids]
        
        # Generate set combinations from SET1~3 groups (generalized logic)
        set1_selected = st.session_state.get('set1_selected', [])
        set2_selected = st.session_state.get('set2_selected', [])
        set3_selected = st.session_state.get('set3_selected', [])
        set_groups = [set1_selected, set2_selected, set3_selected]
        combinations = generate_set_combinations(set_groups)
        
        # Debug: Show combination generation info
        if combinations:
            st.info(f"생성된 조합: {len(combinations)}개 - {combinations}")
        elif any(set_groups):
            st.warning(f"조합 생성 실패: 그룹={set_groups}, 필터링 후 룬 수={len(filtered_runes)}")
        
        strict_mode = st.session_state.get('strict_sets', True)
        
        # If no combinations, run without set constraints
        if not combinations:
            # No set groups specified - run with all sets allowed (except excluded)
            with st.spinner("최적화 실행 중..."):
                try:
                    result = run_search(
                        runes=filtered_runes,
                        monster=monster,
                        base_atk=base_atk,
                        base_spd=base_spd,
                        base_hp=base_hp,
                        base_def=base_def,
                        constraints=constraints,
                        set_constraints=None,
                        objective=objective,
                        top_n=top_n,
                        return_all=return_all,
                        mode=mode
                    )
                    all_results = result.get('results', [])
                except Exception as e:
                    st.error(f"❌ 최적화 오류: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    all_results = []
        else:
            # Run optimization for each combination
            all_results = []
            set_name_to_id = {v: k for k, v in SET_ID_NAME.items()}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, combo in enumerate(combinations):
                status_text.text(f"조합 {i+1}/{len(combinations)} 처리 중: {' + '.join(combo)}")
                progress_bar.progress((i + 1) / len(combinations))
                
                # Create set_constraints for this combination
                set_constraints = {}
                for set_name in combo:
                    set_constraints[set_name] = get_set_requirement(set_name)
                
                # Filter runes based on strict mode
                combo_filtered_runes = filtered_runes.copy()
                if strict_mode:
                    # Strict: only allow sets in the combination
                    combo_set_ids = [set_name_to_id.get(name) for name in combo if set_name_to_id.get(name)]
                    combo_filtered_runes = [r for r in combo_filtered_runes 
                                           if r.set_id in combo_set_ids or r.intangible]
                
                # Debug: Check if we have enough runes
                slot_runes_count = {}
                for slot in range(1, 7):
                    slot_runes = [r for r in combo_filtered_runes if r.slot == slot]
                    slot_runes_count[slot] = len(slot_runes)
                
                # Check if any slot has no runes
                empty_slots = [slot for slot, count in slot_runes_count.items() if count == 0]
                if empty_slots:
                    st.warning(f"조합 {combo}: 슬롯 {empty_slots}에 룬이 없습니다. (필터링 후 룬 수: {len(combo_filtered_runes)}, 슬롯별: {slot_runes_count})")
                    # Show which sets are available in each slot
                    for slot in empty_slots:
                        all_slot_runes = [r for r in runes if r.slot == slot]
                        slot_sets = set(r.set_name for r in all_slot_runes)
                        st.caption(f"슬롯 {slot} 전체 룬 세트: {sorted(slot_sets)}")
                    continue
                
                # Debug: Show set distribution
                combo_set_ids = [set_name_to_id.get(name) for name in combo if set_name_to_id.get(name)]
                combo_set_counts = {}
                for slot in range(1, 7):
                    slot_runes = [r for r in combo_filtered_runes if r.slot == slot]
                    for rune in slot_runes:
                        set_name = rune.set_name
                        if set_name not in combo_set_counts:
                            combo_set_counts[set_name] = 0
                        combo_set_counts[set_name] += 1
                
                st.caption(f"조합 {combo}: 슬롯별 룬 수={slot_runes_count}, 세트별 룬 수={combo_set_counts}")
                
                try:
                    # Run optimization for this combination
                    combo_result = run_search(
                        runes=combo_filtered_runes,
                        monster=monster,
                        base_atk=base_atk,
                        base_spd=base_spd,
                        base_hp=base_hp,
                        base_def=base_def,
                        constraints=constraints,
                        set_constraints=set_constraints,
                        objective=objective,
                        top_n=top_n * 2,  # Get more results per combo to merge later
                        return_all=False,
                        mode=mode
                    )
                    
                    combo_results = combo_result.get('results', [])
                    if not combo_results:
                        # More detailed debugging
                        st.warning(f"조합 {combo}: 조건을 만족하는 빌드가 없습니다.")
                        with st.expander(f"조합 {combo} 상세 정보"):
                            st.write(f"- 필터링 후 룬 수: {len(combo_filtered_runes)}")
                            st.write(f"- 슬롯별 룬 수: {slot_runes_count}")
                            st.write(f"- 세트 제약: {set_constraints}")
                            st.write(f"- 제약 조건: {constraints}")
                            
                            # Check if we have enough runes for the set requirements
                            combo_set_ids = [set_name_to_id.get(name) for name in combo if set_name_to_id.get(name)]
                            set_counts = {}
                            for rune in combo_filtered_runes:
                                if rune.set_id in combo_set_ids:
                                    set_name = rune.set_name
                                    set_counts[set_name] = set_counts.get(set_name, 0) + 1
                            
                            st.write(f"- 세트별 룬 수: {set_counts}")
                            for set_name, required in set_constraints.items():
                                actual = set_counts.get(set_name, 0)
                                if actual < required:
                                    st.error(f"  {set_name}: 필요 {required}개, 실제 {actual}개 (부족)")
                                else:
                                    st.success(f"  {set_name}: 필요 {required}개, 실제 {actual}개")
                    
                    # Add combo info to each result
                    for build in combo_results:
                        build['_combo'] = combo  # Store which combo this came from
                        all_results.append(build)
                        
                except Exception as e:
                    st.error(f"조합 {combo} 처리 중 오류: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    continue
            
            progress_bar.empty()
            status_text.empty()
            
            # Sort all results by objective and take top N
            if all_results:
                # Sort by score (or objective value)
                all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                all_results = all_results[:top_n]
        
        # Post-process: Filter out broken sets if no_broken_sets is enabled
        if st.session_state.get('no_broken_sets', False):
            from collections import Counter
            valid_results = []
            for build in all_results:
                slots = build.get('slots', {})
                set_counts = Counter()
                for slot_num, slot_info in slots.items():
                    set_name = slot_info.get('set_name', '')
                    if set_name and set_name != "Unknown":
                        set_counts[set_name] += 1
                
                # Check if all sets are complete (2-set or 4-set)
                is_valid = True
                for set_name, count in set_counts.items():
                    required = get_set_requirement(set_name)
                    if count < required:  # Not enough for completion
                        is_valid = False
                        break
                    # Check for broken sets (not 2, 4, or 6)
                    if count not in [0, 2, 4, 6]:
                        is_valid = False
                        break
                
                if is_valid:
                    valid_results.append(build)
            
            all_results = valid_results
        
        # Post-process: Apply MIN/MAX filters if filters are applied
        if st.session_state.get('filters_applied', False):
            filtered_results = []
            filters = st.session_state.get('filters', {})
            
            for build in all_results:
                is_valid = True
                
                # Check each filter
                for stat, limits in filters.items():
                    if limits['min'] is None and limits['max'] is None:
                        continue
                    
                    # Get build value
                    build_value = None
                    if stat == 'HP_TOTAL':
                        build_value = build.get('hp_total', 0)
                    elif stat == 'ATK_TOTAL':
                        build_value = build.get('atk_total', 0)
                    elif stat == 'DEF_TOTAL':
                        build_value = build.get('def_total', 0)
                    elif stat == 'SPD':
                        build_value = build.get('spd_total', 0)
                    elif stat == 'CRIT':
                        build_value = build.get('cr_total', 0)
                    elif stat == 'CRITDMG':
                        build_value = build.get('cd_total', 0)
                    elif stat == 'ACC':
                        build_value = build.get('acc_total', 0)
                    elif stat == 'RES':
                        build_value = build.get('res_total', 0)
                    elif stat == 'ATK_BONUS':
                        build_value = build.get('atk_bonus', 0)
                    
                    if build_value is not None:
                        # Check MIN
                        if limits['min'] is not None and build_value < limits['min']:
                            is_valid = False
                            break
                        # Check MAX
                        if limits['max'] is not None and build_value > limits['max']:
                            is_valid = False
                            break
                
                if is_valid:
                    filtered_results.append(build)
            
            all_results = filtered_results
        
        # Create final result
        result = {
            "results": all_results,
            "total_found": len(all_results),
            "search_params": {
                "base_atk": base_atk,
                "base_spd": base_spd,
                "base_hp": base_hp,
                "base_def": base_def,
                "constraints": constraints,
                "objective": objective,
                "top_n": top_n,
                "mode": mode,
            },
            "mode": mode,
        }
        
        st.session_state['search_results'] = result
        
        if len(all_results) == 0:
            st.warning(f"⚠️ 조건을 만족하는 빌드가 없습니다.")
            st.info(f"디버그 정보:")
            st.write(f"- 필터링 후 룬 수: {len(filtered_runes)}")
            st.write(f"- 조합 수: {len(combinations)}")
            st.write(f"- 제약 조건: {constraints}")
            if combinations:
                st.write(f"- 조합: {combinations}")
        else:
            st.success(f"✅ {len(all_results)}개 빌드 발견")
        
        st.rerun()


# ===== RESULTS TABLE =====
if st.session_state.get('search_results'):
    st.markdown("---")
    st.markdown('<div class="results-container">', unsafe_allow_html=True)
    st.markdown("### 📊 Results")
    
    results = st.session_state['search_results'].get('results', [])
    
    if results:
        # Initialize pagination state
        if 'results_page' not in st.session_state:
            st.session_state['results_page'] = 0
        
        # Pagination settings
        items_per_page = 10
        total_pages = (len(results) + items_per_page - 1) // items_per_page
        current_page = st.session_state['results_page']
        
        # Calculate slice indices
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(results))
        page_results = results[start_idx:end_idx]
        
        # Prepare table data for current page
        table_data = []
        for i, r in enumerate(page_results, start=start_idx + 1):
            table_data.append({
                "#": i,
                "Score": r.get("score", 0),
                "CR": f"{r.get('cr_total', 0):.1f}",
                "CD": f"{r.get('cd_total', 0):.1f}",
                "ATK": r.get("atk_total", 0),
                "SPD": f"{r.get('spd_total', 0):.1f}",
                "HP": r.get("hp_total", 0),
                "DEF": r.get("def_total", 0),
                "ATK_BONUS": r.get("atk_bonus", 0),
            })
        
        df = pd.DataFrame(table_data)
        
        # Display table with better styling
        st.dataframe(
            df,
            use_container_width=True,
            height=500,
            hide_index=True
        )
        
        # Pagination controls
        pagination_col1, pagination_col2, pagination_col3, pagination_col4 = st.columns([1, 1, 2, 1])
        
        with pagination_col1:
            if st.button("◀ 이전", disabled=(current_page == 0), use_container_width=True):
                st.session_state['results_page'] = max(0, current_page - 1)
                st.rerun()
        
        with pagination_col2:
            if st.button("다음 ▶", disabled=(current_page >= total_pages - 1), use_container_width=True):
                st.session_state['results_page'] = min(total_pages - 1, current_page + 1)
                st.rerun()
        
        with pagination_col3:
            st.caption(f"페이지 {current_page + 1} / {total_pages} | 총 {len(results)}개 빌드 중 {start_idx + 1}-{end_idx}번째 표시")
        
        with pagination_col4:
            # Page jump
            target_page = st.number_input(
                "페이지",
                min_value=1,
                max_value=total_pages,
                value=current_page + 1,
                key="page_jump",
                label_visibility="collapsed"
            )
            if target_page != current_page + 1:
                st.session_state['results_page'] = target_page - 1
                st.rerun()
        
        # Export button (all results)
        col_export1, col_export2 = st.columns([1, 4])
        with col_export1:
            # Prepare full data for export
            full_table_data = []
            for i, r in enumerate(results, 1):
                full_table_data.append({
                    "#": i,
                    "Score": r.get("score", 0),
                    "CR": f"{r.get('cr_total', 0):.1f}",
                    "CD": f"{r.get('cd_total', 0):.1f}",
                    "ATK": r.get("atk_total", 0),
                    "SPD": f"{r.get('spd_total', 0):.1f}",
                    "HP": r.get("hp_total", 0),
                    "DEF": r.get("def_total", 0),
                    "ATK_BONUS": r.get("atk_bonus", 0),
                })
            full_df = pd.DataFrame(full_table_data)
            csv = full_df.to_csv(index=False)
            st.download_button(
                "📥 Export CSV",
                data=csv,
                file_name="rune_builds.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Detailed view (use global index)
        with st.expander("🔍 상세 정보"):
            # Show all results for selection
            selected_global_idx = st.selectbox(
                "빌드 선택",
                range(len(results)),
                format_func=lambda x: f"빌드 #{x+1} (Score: {results[x].get('score', 0)})",
                key="detail_select"
            )
            
            selected = results[selected_global_idx]
            
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
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
            
            with detail_col2:
                st.write("**슬롯별 룬**")
                slots = selected.get("slots", {})
                for slot in range(1, 7):
                    if slot in slots:
                        slot_info = slots[slot]
                        st.write(f"**Slot {slot}:**")
                        st.write(f"- Set: {slot_info.get('set_name', '?')}")
                        st.write(f"- Main: {slot_info.get('main', '?')}")
                        if slot_info.get('prefix'):
                            st.write(f"- Prefix: {slot_info.get('prefix', '?')}")
                        if slot_info.get('subs'):
                            st.write(f"- Subs: {', '.join(slot_info.get('subs', []))}")
    else:
        st.warning("조건을 만족하는 빌드가 없습니다.")
    
    st.markdown('</div>', unsafe_allow_html=True)

