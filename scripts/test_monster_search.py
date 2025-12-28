"""몬스터 검색 기능 테스트"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sw_core.monster_registry import get_registry

def test_search():
    """몬스터 검색 테스트"""
    print("=" * 60)
    print("몬스터 검색 기능 테스트")
    print("=" * 60)
    print()
    
    registry = get_registry(data_dirs=["data"])
    registry.warm_cache()
    
    print(f"캐시된 몬스터 수: {len(registry._cache)}")
    print()
    
    # 테스트 쿼리들
    test_queries = ["루", "Lushen", "베라", "베", "프", "프랑켄"]
    
    for query in test_queries:
        print(f"검색어: '{query}'")
        results = registry.search(query, limit=10)
        print(f"  결과: {len(results)}개")
        for i, stats in enumerate(results[:5], 1):
            name = stats.name_ko or stats.name_en
            if stats.name_ko and stats.name_en:
                name = f"{stats.name_ko} ({stats.name_en})"
            print(f"    {i}. {name} (ID: {stats.master_id})")
        print()

if __name__ == "__main__":
    test_search()


