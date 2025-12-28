"""디버깅 스크립트: 특정 조건으로 최적화 테스트"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from sw_core.api import run_search
from sw_core.swex_parser import parse_swex_json
from sw_core.set_meta import generate_set_combinations, get_set_requirement
from sw_core.types import SET_ID_NAME, STAT_ID_NAME
import json

# Find SWEX JSON file
swex_files = list(project_root.glob("*.json"))
if not swex_files:
    swex_files = list((project_root / "data").glob("*.json"))

if not swex_files:
    print("❌ SWEX JSON 파일을 찾을 수 없습니다.")
    sys.exit(1)

swex_file = swex_files[0]
print(f"[FILE] Loading: {swex_file}")

# Load runes
with open(swex_file, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

runes = parse_swex_json(json_data)
print(f"[OK] {len(runes)} runes loaded")

# Test conditions (from image)
set1_selected = ["Blade"]
set2_selected = ["Fatal", "Rage"]
set3_selected = []
set_groups = [set1_selected, set2_selected, set3_selected]

print(f"\n[TEST CONDITIONS]")
print(f"  SET1: {set1_selected}")
print(f"  SET2: {set2_selected}")
print(f"  SET3: {set3_selected}")

# Generate combinations
from sw_core.set_meta import generate_set_combinations
combinations = generate_set_combinations(set_groups)
print(f"\n[COMBINATIONS] {len(combinations)} generated")
for i, combo in enumerate(combinations, 1):
    print(f"  {i}. {combo}")

# Constraints from image
constraints = {
    "ATK_TOTAL": 1900,
    "CR": 100
}

print(f"\n[CONSTRAINTS]")
print(f"  ATK_TOTAL >= {constraints['ATK_TOTAL']}")
print(f"  CR >= {constraints['CR']}")

# Test each combination
set_name_to_id = {v: k for k, v in SET_ID_NAME.items()}

for combo in combinations:
    print(f"\n{'='*60}")
    print(f"[TEST COMBO] {combo}")
    print(f"{'='*60}")
    
    # Create set_constraints
    set_constraints = {}
    for set_name in combo:
        set_constraints[set_name] = get_set_requirement(set_name)
    
    print(f"Set constraints: {set_constraints}")
    
    # Filter runes (strict mode)
    combo_set_ids = [set_name_to_id.get(name) for name in combo if set_name_to_id.get(name)]
    print(f"Required set IDs: {combo_set_ids}")
    
    filtered_runes = [r for r in runes if r.set_id in combo_set_ids or r.intangible]
    print(f"Filtered runes: {len(filtered_runes)}")
    
    # Check slot distribution
    slot_runes_count = {}
    for slot in range(1, 7):
        slot_runes = [r for r in filtered_runes if r.slot == slot]
        slot_runes_count[slot] = len(slot_runes)
    
    print(f"Runes per slot: {slot_runes_count}")
    
    # Check set distribution
    set_counts = {}
    for rune in filtered_runes:
        set_name = rune.set_name
        set_counts[set_name] = set_counts.get(set_name, 0) + 1
    
    print(f"Runes per set: {set_counts}")
    
    # Check if we have enough for set requirements
    for set_name, required in set_constraints.items():
        actual = set_counts.get(set_name, 0)
        status = "[OK]" if actual >= required else "[FAIL]"
        print(f"  {status} {set_name}: need {required}, have {actual}")
    
    # Check for empty slots
    empty_slots = [slot for slot, count in slot_runes_count.items() if count == 0]
    if empty_slots:
        print(f"[WARN] Empty slots: {empty_slots}")
        for slot in empty_slots:
            all_slot_runes = [r for r in runes if r.slot == slot]
            slot_sets = set(r.set_name for r in all_slot_runes)
            print(f"  Slot {slot} all sets: {sorted(slot_sets)}")
        continue
    
    # Run optimization
    print(f"\n[OPTIMIZE] Running...")
    try:
        result = run_search(
            runes=filtered_runes,
            base_atk=900,  # Default
            base_spd=104,
            base_hp=10000,
            base_def=500,
            constraints=constraints,
            set_constraints=set_constraints,
            objective="SCORE",
            top_n=20,
            return_all=False,
            mode="exhaustive"
        )
        
        results = result.get('results', [])
        print(f"[RESULT] {len(results)} builds found")
        
        if results:
            print(f"\nTop 3 builds:")
            for i, build in enumerate(results[:3], 1):
                print(f"  {i}. Score: {build.get('score', 0):.1f}, "
                      f"ATK: {build.get('atk_total', 0)}, "
                      f"CR: {build.get('cr_total', 0):.1f}%")
        else:
            print(f"[FAIL] No builds found matching constraints")
            print(f"\n[DEBUG INFO]")
            print(f"  - Filtered runes: {len(filtered_runes)}")
            print(f"  - Runes per slot: {slot_runes_count}")
            print(f"  - Runes per set: {set_counts}")
            print(f"  - Constraints: {constraints}")
            print(f"  - Set constraints: {set_constraints}")
            
            # Try without constraints to see if we get any results
            print(f"\n[TEST] Running without constraints...")
            result_no_constraints = run_search(
                runes=filtered_runes,
                base_atk=900,
                base_spd=104,
                base_hp=10000,
                base_def=500,
                constraints={},
                set_constraints=set_constraints,
                objective="SCORE",
                top_n=5,
                return_all=False,
                mode="exhaustive"
            )
            no_const_results = result_no_constraints.get('results', [])
            if no_const_results:
                print(f"[OK] Without constraints: {len(no_const_results)} builds found")
                print(f"Top build stats:")
                for build in no_const_results[:3]:
                    print(f"  - ATK: {build.get('atk_total', 0)}, CR: {build.get('cr_total', 0):.1f}%")
            else:
                print(f"[FAIL] No builds even without constraints. Set constraint issue?")
                
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print("[DONE] Debugging complete")

