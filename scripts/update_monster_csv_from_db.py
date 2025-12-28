"""DB에서 몬스터 데이터를 가져와서 CSV 업데이트"""

import sys
import csv
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sw_mcp.db.repo import SwarfarmRepository
from sw_mcp.db.models import SwarfarmRaw


def update_monster_csv_from_db():
    """DB에서 몬스터 데이터를 가져와서 CSV 업데이트"""
    print("=" * 60)
    print("DB에서 몬스터 CSV 파일 업데이트")
    print("=" * 60)
    print()
    
    repo = SwarfarmRepository()
    
    try:
        print("[1] DB에서 몬스터 데이터 조회...")
        monsters_raw = repo.session.query(SwarfarmRaw).filter(
            SwarfarmRaw.endpoint == "monsters"
        ).all()
        
        print(f"   DB에 저장된 몬스터 수: {len(monsters_raw)}")
        
        if len(monsters_raw) == 0:
            print()
            print("[WARN] DB에 몬스터 데이터가 없습니다.")
            print("   먼저 다음 명령을 실행하세요:")
            print("   python -m sw_mcp.cli swarfarm-sync --endpoint monsters")
            return False
        
        print()
        print("[2] 몬스터 데이터 파싱 및 변환...")
        monsters = []
        
        for raw in monsters_raw:
            try:
                monster_data = json.loads(raw.payload_json)
                
                com2us_id = monster_data.get("com2us_id")
                if not com2us_id:
                    continue
                
                name_en = monster_data.get("name", "")
                name_ko = monster_data.get("name_ko", "") or name_en
                
                # 기본 스탯 추출
                base_stats = monster_data.get("base_stats", {})
                if not base_stats:
                    base_stats = {
                        "hp": monster_data.get("base_hp", 0),
                        "attack": monster_data.get("base_attack", 0),
                        "defense": monster_data.get("base_defense", 0),
                        "speed": monster_data.get("speed", 0),
                    }
                
                element = monster_data.get("element", "")
                awakened = monster_data.get("awakened", True)
                nat_stars = monster_data.get("natural_stars", monster_data.get("base_stars", 4))
                
                monsters.append({
                    "master_id": com2us_id,
                    "name_en": name_en,
                    "name_ko": name_ko,
                    "element": element,
                    "awakened": "true" if awakened else "false",
                    "nat_stars": nat_stars,
                    "base_hp": base_stats.get("hp", 0),
                    "base_atk": base_stats.get("attack", 0),
                    "base_def": base_stats.get("defense", 0),
                    "base_spd": base_stats.get("speed", 0),
                    "base_cr": 15,
                    "base_cd": 50,
                })
            except Exception as e:
                print(f"   Warning: 몬스터 파싱 실패: {e}")
                continue
        
        print(f"   파싱 완료: {len(monsters)}개 몬스터")
        print()
        
        # 비바첼, 탄지로 확인
        print("[3] 특정 몬스터 확인:")
        vivachel = [m for m in monsters if "vivachel" in m["name_en"].lower() or "비바첼" in m["name_ko"]]
        tangiro = [m for m in monsters if "tangiro" in m["name_en"].lower() or "탄지로" in m["name_ko"]]
        
        if vivachel:
            print(f"   [OK] 비바첼 발견: {vivachel[0]['name_ko']} ({vivachel[0]['name_en']}) - ID: {vivachel[0]['master_id']}")
        else:
            print("   [WARN] 비바첼: 없음")
        
        if tangiro:
            print(f"   [OK] 탄지로 발견: {tangiro[0]['name_ko']} ({tangiro[0]['name_en']}) - ID: {tangiro[0]['master_id']}")
        else:
            print("   [WARN] 탄지로: 없음")
        print()
        
        # 이름으로 정렬
        monsters.sort(key=lambda x: (x["name_ko"] or x["name_en"]).lower())
        
        # CSV 저장
        csv_path = Path("data/monsters_v1.csv")
        csv_path.parent.mkdir(exist_ok=True)
        
        print(f"[4] CSV 파일 저장: {csv_path}")
        fieldnames = [
            "master_id", "name_en", "name_ko", "element", "awakened",
            "nat_stars", "base_hp", "base_atk", "base_def", "base_spd",
            "base_cr", "base_cd"
        ]
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(monsters)
        
        print(f"   완료: {len(monsters)}개 몬스터 저장됨")
        print()
        print("=" * 60)
        print("업데이트 완료!")
        print("=" * 60)
        print()
        print(f"총 {len(monsters)}개 몬스터가 CSV 파일에 저장되었습니다.")
        print(f"파일 위치: {csv_path.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        repo.close()


if __name__ == "__main__":
    success = update_monster_csv_from_db()
    sys.exit(0 if success else 1)


