"""몬스터 데이터 확인 스크립트"""

import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sw_core.monster_registry import get_registry

def check_monsters():
    """몬스터 데이터 확인"""
    print("=" * 60)
    print("몬스터 데이터 확인")
    print("=" * 60)
    print()
    
    # CSV 파일 직접 확인
    csv_path = Path("data/monsters_v1.csv")
    if csv_path.exists():
        print(f"[1] CSV 파일 확인: {csv_path}")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"   총 몬스터 수: {len(rows)}")
            print()
            print("   샘플 (처음 10개):")
            for i, row in enumerate(rows[:10], 1):
                name_ko = row.get('name_ko', '')
                name_en = row.get('name_en', '')
                master_id = row.get('master_id', '')
                print(f"   {i}. {name_ko} ({name_en}) - ID: {master_id}")
            print()
    else:
        print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
        return
    
    # 레지스트리 확인
    print("[2] 레지스트리 확인:")
    registry = get_registry(data_dirs=["data"])
    registry.warm_cache()
    print(f"   캐시된 몬스터 수: {len(registry._cache)}")
    print(f"   이름 매핑 수: {len(registry._name_to_id)}")
    print()
    
    # 검색 테스트
    print("[3] 검색 테스트:")
    test_queries = ["루", "Lushen", "베라", "베", "시그"]
    for query in test_queries:
        results = registry.search(query, limit=10)
        print(f"   '{query}': {len(results)}개")
        for stats in results[:3]:
            name = stats.name_ko or stats.name_en
            if stats.name_ko and stats.name_en:
                name = f"{stats.name_ko} ({stats.name_en})"
            print(f"      - {name} (ID: {stats.master_id})")
    print()
    
    # 누락 확인
    print("[4] 누락 확인:")
    csv_monsters = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            master_id = int(row.get('master_id', 0))
            csv_monsters.add(master_id)
    
    registry_monsters = set(registry._cache.keys())
    missing = csv_monsters - registry_monsters
    extra = registry_monsters - csv_monsters
    
    if missing:
        print(f"   레지스트리에 없는 몬스터: {len(missing)}개")
        print(f"   {list(missing)[:10]}")
    else:
        print("   [OK] 모든 CSV 몬스터가 레지스트리에 로드됨")
    
    if extra:
        print(f"   CSV에 없는 몬스터: {len(extra)}개")
    else:
        print("   ✓ 레지스트리와 CSV 일치")

if __name__ == "__main__":
    check_monsters()

