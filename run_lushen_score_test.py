"""루쉔 룬 조합 테스트 스크립트"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from sw_core.api import run_search
from sw_core.swex_parser import load_swex_json
from sw_core.optimizer import search_builds
from sw_core.monster_registry import get_registry


def format_rune_detail(rune) -> Dict[str, Any]:
    """룬 상세 정보 포맷팅"""
    # 서브 스탯 중 ATK%, ATK+, CR, CD만 필터링
    relevant_subs = []
    for sub in rune.subs:
        if sub.stat_id in [4, 3, 9, 10]:  # ATK%, ATK+, CR, CD
            stat_name = {
                4: "ATK%",
                3: "ATK+",
                9: "CR",
                10: "CD"
            }.get(sub.stat_id, "?")
            relevant_subs.append(f"{stat_name} {sub.value}")
    
    result = {
        "slot": rune.slot,
        "rune_id": rune.rune_id,
        "set": rune.set_name,
        "main_stat": rune.main_stat_name,
        "main_value": rune.main_stat_value,
    }
    
    if rune.has_prefix:
        result["prefix"] = f"{rune.prefix_stat_name} {rune.prefix_stat_value}"
    else:
        result["prefix"] = None
    
    result["relevant_subs"] = relevant_subs
    
    return result


def main():
    # 입력 파일 찾기
    json_file = None
    possible_names = [
        "테오니아-1164562.json",
        "테오니아-1164562.JSON",
        "테오니아-1164562",
    ]
    
    # 현재 디렉토리에서 찾기
    for name in possible_names:
        if Path(name).exists():
            json_file = name
            break
    
    # 없으면 모든 JSON 파일 검색
    if not json_file:
        json_files = list(Path(".").glob("*.json"))
        if json_files:
            print("Available JSON files:")
            for i, f in enumerate(json_files, 1):
                print(f"  {i}. {f.name}")
            # 첫 번째 파일 사용
            if len(json_files) == 1:
                json_file = str(json_files[0])
                print(f"Using: {json_file}")
            else:
                print(f"\nUsing first file: {json_files[0].name}")
                json_file = str(json_files[0])
    
    # 명령줄 인자로 파일 경로 지정 가능
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        print(f"Using file from command line: {json_file}")
    
    if not json_file or not Path(json_file).exists():
        print(f"Error: JSON file not found")
        print("Please place '테오니아-1164562.json' in the current directory")
        sys.exit(1)
    
    print(f"Loading SWEX JSON: {json_file}")
    runes = load_swex_json(json_file)
    print(f"Loaded {len(runes)} runes")
    
    # 레지스트리에서 루쉔 정보 조회
    registry = get_registry()
    lushen_stats = registry.get(name="Lushen")
    if lushen_stats:
        base_atk = lushen_stats.base_atk
        base_spd = lushen_stats.base_spd
        base_hp = lushen_stats.base_hp
        base_def = lushen_stats.base_def
        base_cr = lushen_stats.base_cr
        base_cd = lushen_stats.base_cd
        print(f"Lushen stats from registry: ATK={base_atk}, SPD={base_spd}, CR={base_cr}, CD={base_cd}")
    else:
        # 기본값 사용
        base_atk = 900
        base_spd = 104
        base_hp = 10000
        base_def = 500
        base_cr = 15
        base_cd = 50
        print(f"Lushen not found in registry, using defaults: ATK={base_atk}, CR={base_cr}, CD={base_cd}")
    
    # 제약 조건
    constraints = {"CR": 100}
    
    # 출력 디렉토리 생성
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    
    results = {}
    
    # A) Rage 4 + Blade 2
    print("\n" + "="*60)
    print("A) Rage(격노) 4 + Blade(칼날) 2 탐색")
    print("="*60)
    
    # search_builds를 직접 호출하여 base_cd, base_cr을 명시적으로 전달
    print(f"Searching with constraints: CR >= {constraints['CR']}")
    print(f"Set constraints: Rage >= 4, Blade >= 2")
    print(f"Mode: exhaustive (100% accuracy)")
    
    result_a_list = search_builds(
        runes=runes,
        base_atk=base_atk,
        base_spd=base_spd,
        base_hp=base_hp,
        base_def=base_def,
        base_cr=base_cr,
        base_cd=base_cd,
        constraints=constraints,
        set_constraints={"Rage": 4, "Blade": 2},
        objective="SCORE",
        top_n=1,
        mode="exhaustive"  # 정확도 100% 보장
    )
    
    print(f"Found {len(result_a_list)} results for A")
    
    result_a = {"results": result_a_list}
    
    if result_a["results"]:
        best_a = result_a["results"][0]
        results["A"] = best_a
        
        stats_a = best_a["stats"]
        print(f"\n[최고 점수] {best_a['score']:.1f}")
        print(f"  total_CR: {stats_a.get('cr_total', 0):.1f}")
        print(f"  total_CD: {stats_a.get('cd_total', 0):.1f}")
        print(f"  atk_bonus: {stats_a.get('atk_bonus', 0)}")
        print(f"  atk_pct_total: {stats_a.get('atk_pct_total', 0):.1f}")
        print(f"  atk_flat_total: {stats_a.get('atk_flat_total', 0):.1f}")
        print(f"  intangible_assignment: {best_a.get('intangible_assignment', 'none')}")
        
        print("\n[6개 룬 상세]")
        slots_a = best_a.get("slots", {})
        for slot in range(1, 7):
            if slot in slots_a:
                slot_info = slots_a[slot]
                print(f"  Slot {slot}:")
                print(f"    rune_id: {slot_info.get('rune_id')}")
                print(f"    set: {slot_info.get('set_name')}")
                print(f"    main: {slot_info.get('main')}")
                if slot_info.get('prefix'):
                    print(f"    prefix: {slot_info.get('prefix')}")
                if slot_info.get('subs'):
                    print(f"    subs: {', '.join(slot_info.get('subs', []))}")
    else:
        print("조건을 만족하는 빌드를 찾을 수 없습니다.")
        results["A"] = None
    
    # B) Fatal 4 + Blade 2
    print("\n" + "="*60)
    print("B) Fatal(맹공) 4 + Blade(칼날) 2 탐색")
    print("="*60)
    
    print(f"Searching with constraints: CR >= {constraints['CR']}")
    print(f"Set constraints: Fatal >= 4, Blade >= 2")
    print(f"Mode: exhaustive (100% accuracy)")
    
    result_b_list = search_builds(
        runes=runes,
        base_atk=base_atk,
        base_spd=base_spd,
        base_hp=base_hp,
        base_def=base_def,
        base_cr=base_cr,
        base_cd=base_cd,
        constraints=constraints,
        set_constraints={"Fatal": 4, "Blade": 2},
        objective="SCORE",
        top_n=1,
        mode="exhaustive"
    )
    
    print(f"Found {len(result_b_list)} results for B")
    
    result_b = {"results": result_b_list}
    
    if result_b["results"]:
        best_b = result_b["results"][0]
        results["B"] = best_b
        
        stats_b = best_b["stats"]
        print(f"\n[최고 점수] {best_b['score']:.1f}")
        print(f"  total_CR: {stats_b.get('cr_total', 0):.1f}")
        print(f"  total_CD: {stats_b.get('cd_total', 0):.1f}")
        print(f"  atk_bonus: {stats_b.get('atk_bonus', 0)}")
        print(f"  atk_pct_total: {stats_b.get('atk_pct_total', 0):.1f}")
        print(f"  atk_flat_total: {stats_b.get('atk_flat_total', 0):.1f}")
        print(f"  intangible_assignment: {best_b.get('intangible_assignment', 'none')}")
        
        print("\n[6개 룬 상세]")
        slots_b = best_b.get("slots", {})
        for slot in range(1, 7):
            if slot in slots_b:
                slot_info = slots_b[slot]
                print(f"  Slot {slot}:")
                print(f"    rune_id: {slot_info.get('rune_id')}")
                print(f"    set: {slot_info.get('set_name')}")
                print(f"    main: {slot_info.get('main')}")
                if slot_info.get('prefix'):
                    print(f"    prefix: {slot_info.get('prefix')}")
                if slot_info.get('subs'):
                    print(f"    subs: {', '.join(slot_info.get('subs', []))}")
    else:
        print("조건을 만족하는 빌드를 찾을 수 없습니다.")
        results["B"] = None
    
    # 결과 저장
    print("\n" + "="*60)
    print("결과 저장 중...")
    print("="*60)
    
    # A 결과 저장
    if results["A"]:
        output_a = {
            "build_type": "A_Rage_Blade",
            "score": results["A"]["score"],
            "stats": {
                "total_CR": results["A"]["stats"].get("cr_total", 0),
                "total_CD": results["A"]["stats"].get("cd_total", 0),
                "atk_bonus": results["A"]["stats"].get("atk_bonus", 0),
                "atk_pct_total": results["A"]["stats"].get("atk_pct_total", 0),
                "atk_flat_total": results["A"]["stats"].get("atk_flat_total", 0),
                "atk_total": results["A"]["stats"].get("atk_total", 0),
            },
            "intangible_assignment": results["A"].get("intangible_assignment", "none"),
            "runes": []
        }
        
        slots_a = results["A"].get("slots", {})
        for slot in range(1, 7):
            if slot in slots_a:
                slot_info = slots_a[slot]
                rune_detail = {
                    "slot": slot,
                    "rune_id": slot_info.get("rune_id"),
                    "set": slot_info.get("set_name"),
                    "main": slot_info.get("main"),
                    "prefix": slot_info.get("prefix"),
                    "subs": slot_info.get("subs", [])
                }
                output_a["runes"].append(rune_detail)
        
        with open(out_dir / "lushen_A_rage_blade_best.json", "w", encoding="utf-8") as f:
            json.dump(output_a, f, ensure_ascii=False, indent=2)
        print(f"Saved: {out_dir / 'lushen_A_rage_blade_best.json'}")
    
    # B 결과 저장
    if results["B"]:
        output_b = {
            "build_type": "B_Fatal_Blade",
            "score": results["B"]["score"],
            "stats": {
                "total_CR": results["B"]["stats"].get("cr_total", 0),
                "total_CD": results["B"]["stats"].get("cd_total", 0),
                "atk_bonus": results["B"]["stats"].get("atk_bonus", 0),
                "atk_pct_total": results["B"]["stats"].get("atk_pct_total", 0),
                "atk_flat_total": results["B"]["stats"].get("atk_flat_total", 0),
                "atk_total": results["B"]["stats"].get("atk_total", 0),
            },
            "intangible_assignment": results["B"].get("intangible_assignment", "none"),
            "runes": []
        }
        
        slots_b = results["B"].get("slots", {})
        for slot in range(1, 7):
            if slot in slots_b:
                slot_info = slots_b[slot]
                rune_detail = {
                    "slot": slot,
                    "rune_id": slot_info.get("rune_id"),
                    "set": slot_info.get("set_name"),
                    "main": slot_info.get("main"),
                    "prefix": slot_info.get("prefix"),
                    "subs": slot_info.get("subs", [])
                }
                output_b["runes"].append(rune_detail)
        
        with open(out_dir / "lushen_B_fatal_blade_best.json", "w", encoding="utf-8") as f:
            json.dump(output_b, f, ensure_ascii=False, indent=2)
        print(f"Saved: {out_dir / 'lushen_B_fatal_blade_best.json'}")
    
    # CSV 요약 저장
    import csv
    
    with open(out_dir / "lushen_best_summary.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Build", "Score", "total_CR", "total_CD", "atk_bonus",
            "atk_pct_total", "atk_flat_total", "atk_total", "intangible_assignment"
        ])
        
        if results["A"]:
            stats_a = results["A"]["stats"]
            writer.writerow([
                "A_Rage_Blade",
                f"{results['A']['score']:.1f}",
                f"{stats_a.get('cr_total', 0):.1f}",
                f"{stats_a.get('cd_total', 0):.1f}",
                stats_a.get("atk_bonus", 0),
                f"{stats_a.get('atk_pct_total', 0):.1f}",
                f"{stats_a.get('atk_flat_total', 0):.1f}",
                stats_a.get("atk_total", 0),
                results["A"].get("intangible_assignment", "none")
            ])
        
        if results["B"]:
            stats_b = results["B"]["stats"]
            writer.writerow([
                "B_Fatal_Blade",
                f"{results['B']['score']:.1f}",
                f"{stats_b.get('cr_total', 0):.1f}",
                f"{stats_b.get('cd_total', 0):.1f}",
                stats_b.get("atk_bonus", 0),
                f"{stats_b.get('atk_pct_total', 0):.1f}",
                f"{stats_b.get('atk_flat_total', 0):.1f}",
                stats_b.get("atk_total", 0),
                results["B"].get("intangible_assignment", "none")
            ])
    
    print(f"Saved: {out_dir / 'lushen_best_summary.csv'}")
    
    print("\n" + "="*60)
    print("완료!")
    print("="*60)
    
    # 최종 요약
    if results["A"] and results["B"]:
        print(f"\nA (Rage+Blade) 최고 점수: {results['A']['score']:.1f}")
        print(f"B (Fatal+Blade) 최고 점수: {results['B']['score']:.1f}")
        if results["A"]["score"] > results["B"]["score"]:
            print("→ A가 더 높은 점수")
        elif results["B"]["score"] > results["A"]["score"]:
            print("→ B가 더 높은 점수")
        else:
            print("→ 동점")


if __name__ == "__main__":
    main()

