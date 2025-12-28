"""상세 디버깅: 세트 제약 조건 검증"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from sw_core.swex_parser import parse_swex_json
from sw_core.set_meta import generate_set_combinations, get_set_requirement
from sw_core.types import SET_ID_NAME
from sw_core.scoring import count_sets, score_build
import json

# Find SWEX JSON file
swex_files = list(project_root.glob("*.json"))
if not swex_files:
    swex_files = list((project_root / "data").glob("*.json"))

if not swex_files:
    print("[ERROR] SWEX JSON file not found")
    sys.exit(1)

swex_file = swex_files[0]
print(f"[FILE] Loading: {swex_file}")

# Load runes
with open(swex_file, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

runes = parse_swex_json(json_data)
print(f"[OK] {len(runes)} runes loaded")

# Test combo: Blade + Fatal
combo = ("Blade", "Fatal")
set_constraints = {"Blade": 2, "Fatal": 4}

print(f"\n[TEST] Combo: {combo}")
print(f"Set constraints: {set_constraints}")

# Filter runes
set_name_to_id = {v: k for k, v in SET_ID_NAME.items()}
combo_set_ids = [set_name_to_id.get(name) for name in combo if set_name_to_id.get(name)]
filtered_runes = [r for r in runes if r.set_id in combo_set_ids or r.intangible]

print(f"Filtered runes: {len(filtered_runes)}")
print(f"Required set IDs: {combo_set_ids}")

# Check slot distribution
slot_runes = {}
for slot in range(1, 7):
    slot_runes[slot] = [r for r in filtered_runes if r.slot == slot]
    print(f"Slot {slot}: {len(slot_runes[slot])} runes")

# Try to manually create a valid build
print(f"\n[MANUAL BUILD TEST]")
print("Trying to create a valid build manually...")

# Count available runes per set per slot
for slot in range(1, 7):
    slot_rune_sets = {}
    for rune in slot_runes[slot]:
        set_name = rune.set_name
        slot_rune_sets[set_name] = slot_rune_sets.get(set_name, 0) + 1
    print(f"Slot {slot} sets: {slot_rune_sets}")

# Try to find a valid combination
print(f"\n[BUILD SEARCH]")
print("Searching for valid builds...")

from sw_core.optimizer import search_builds

result = search_builds(
    runes=filtered_runes,
    base_atk=900,
    base_spd=104,
    base_hp=10000,
    base_def=500,
    constraints={},  # No stat constraints first
    set_constraints=set_constraints,
    objective="SCORE",
    top_n=5,
    return_all=False,
    mode="exhaustive"
)

print(f"Results: {len(result)} builds")

if result:
    print(f"\n[SUCCESS] Found {len(result)} builds")
    for i, build in enumerate(result[:3], 1):
        print(f"  {i}. Score: {build.get('score', 0):.1f}")
        # Check set counts
        slots = build.get('slots', {})
        set_counts = {}
        for slot_num, slot_info in slots.items():
            set_name = slot_info.get('set_name', '')
            if set_name:
                set_counts[set_name] = set_counts.get(set_name, 0) + 1
        print(f"     Sets: {set_counts}")
else:
    print(f"[FAIL] No builds found")
    print(f"\n[DEBUG] Checking why...")
    
    # Check if we can create any build at all
    print(f"\n[TEST] Without set constraints...")
    result_no_set = search_builds(
        runes=filtered_runes,
        base_atk=900,
        base_spd=104,
        base_hp=10000,
        base_def=500,
        constraints={},
        set_constraints={},  # No set constraints
        objective="SCORE",
        top_n=5,
        return_all=False,
        mode="exhaustive"
    )
    print(f"Results without set constraints: {len(result_no_set)} builds")
    
    if result_no_set:
        print(f"[INFO] Can create builds, but set constraints are too strict")
        # Check set distribution in results
        for build in result_no_set[:3]:
            slots = build.get('slots', {})
            set_counts = {}
            for slot_num, slot_info in slots.items():
                set_name = slot_info.get('set_name', '')
                if set_name:
                    set_counts[set_name] = set_counts.get(set_name, 0) + 1
            print(f"  Sets in build: {set_counts}")
    else:
        print(f"[ERROR] Cannot create any builds even without constraints!")


