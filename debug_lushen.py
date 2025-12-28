"""디버깅: 룬 데이터 확인"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sw_core.swex_parser import load_swex_json
from sw_core.rules import filter_valid_runes
from collections import Counter

json_file = "테오니아-1164562.json"
runes = load_swex_json(json_file)
print(f"Total runes loaded: {len(runes)}")

# 유효한 룬만 필터링
valid_runes = filter_valid_runes(runes)
print(f"Valid runes: {len(valid_runes)}")

# 슬롯별 룬 개수
slots = Counter(r.slot for r in valid_runes)
print(f"\nRunes per slot:")
for slot in sorted(slots.keys()):
    print(f"  Slot {slot}: {slots[slot]}")

# 세트별 룬 개수
sets = Counter(r.set_id for r in valid_runes)
print(f"\nRunes per set:")
for set_id, count in sets.most_common(20):
    set_name = {5: "Rage", 8: "Fatal", 4: "Blade"}.get(set_id, f"Set_{set_id}")
    print(f"  {set_name} (ID={set_id}): {count}")

# Rage, Fatal, Blade 룬 개수
rage_count = sum(1 for r in valid_runes if r.set_id == 5)
fatal_count = sum(1 for r in valid_runes if r.set_id == 8)
blade_count = sum(1 for r in valid_runes if r.set_id == 4)
print(f"\nTarget sets:")
print(f"  Rage: {rage_count}")
print(f"  Fatal: {fatal_count}")
print(f"  Blade: {blade_count}")

# CR 스탯이 있는 룬 확인
cr_runes = [r for r in valid_runes if any(sub.stat_id == 9 for sub in r.subs) or r.main_stat_id == 9]
print(f"\nRunes with CR stat: {len(cr_runes)}")

# 샘플 룬 확인 (Rage/Blade 조합 가능한지)
print(f"\nSample Rage runes (first 5):")
rage_runes = [r for r in valid_runes if r.set_id == 5][:5]
for r in rage_runes:
    cr_subs = [sub for sub in r.subs if sub.stat_id == 9]
    print(f"  Slot {r.slot}, CR subs: {[s.value for s in cr_subs]}")

print(f"\nSample Blade runes (first 5):")
blade_runes = [r for r in valid_runes if r.set_id == 4][:5]
for r in blade_runes:
    cr_subs = [sub for sub in r.subs if sub.stat_id == 9]
    print(f"  Slot {r.slot}, CR subs: {[s.value for s in cr_subs]}")


