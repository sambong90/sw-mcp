"""CR 조건 없이 테스트"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sw_core.swex_parser import load_swex_json
from sw_core.optimizer import search_builds
from sw_core.monster_registry import get_registry

json_file = "테오니아-1164562.json"
runes = load_swex_json(json_file)
print(f"Loaded {len(runes)} runes")

# 루쉔 스탯
registry = get_registry()
lushen_stats = registry.get(name="Lushen")
if lushen_stats:
    base_atk = lushen_stats.base_atk
    base_cr = lushen_stats.base_cr
    base_cd = lushen_stats.base_cd
else:
    base_atk = 900
    base_cr = 15
    base_cd = 50

print(f"Base stats: ATK={base_atk}, CR={base_cr}, CD={base_cd}")

# A) Rage + Blade (CR 조건 없음)
print("\n=== A) Rage 4 + Blade 2 (CR 조건 없음) ===")
result_a = search_builds(
    runes=runes,
    base_atk=base_atk,
    base_spd=110,
    base_hp=10000,
    base_def=500,
    base_cr=base_cr,
    base_cd=base_cd,
    constraints={},  # CR 조건 없음
    set_constraints={"Rage": 4, "Blade": 2},
    objective="SCORE",
    top_n=5,
    mode="fast"  # 빠른 테스트
)

print(f"Found {len(result_a)} builds")
if result_a:
    for i, build in enumerate(result_a[:3], 1):
        stats = build["stats"]
        print(f"\nBuild {i}:")
        print(f"  Score: {build['score']:.1f}")
        print(f"  CR: {stats.get('cr_total', 0):.1f} (base={base_cr}, runes={stats.get('cr_total', 0) - base_cr:.1f}, Blade bonus=12)")
        print(f"  CD: {stats.get('cd_total', 0):.1f} (base={base_cd}, runes={stats.get('cd_total', 0) - base_cd - 40:.1f}, Rage bonus=40)")
        print(f"  ATK bonus: {stats.get('atk_bonus', 0)}")
        print(f"  ATK% total: {stats.get('atk_pct_total', 0):.1f}")
        print(f"  ATK+ total: {stats.get('atk_flat_total', 0):.1f}")


