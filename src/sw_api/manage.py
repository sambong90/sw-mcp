"""관리 커맨드: 몬스터 데이터 seed/export"""

import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.sw_db.models import get_session, Monster, Base, get_engine
from src.sw_core.monster_registry import MonsterRegistry
from src.sw_core.types import MonsterBaseStats


def seed_monsters(csv_path: str, db_url: str = "sqlite:///sw_mcp.db"):
    """CSV 파일에서 몬스터 데이터를 DB에 seed"""
    print(f"Loading monsters from {csv_path}...")
    
    session = get_session(db_url)
    registry = MonsterRegistry(data_dirs=["data"])
    
    # CSV에서 로드
    monsters = registry._load_csv(csv_path)
    
    if not monsters:
        print(f"Warning: No monsters found in {csv_path}")
        return
    
    print(f"Found {len(monsters)} monsters in CSV")
    
    # DB에 upsert
    upserted = 0
    for master_id, stats in monsters.items():
        existing = session.query(Monster).filter(
            Monster.master_id == master_id
        ).first()
        
        if existing:
            # 업데이트
            existing.name_ko = stats.name_ko
            existing.name_en = stats.name_en
            existing.element = stats.element
            existing.awakened = stats.awakened
            existing.nat_stars = stats.nat_stars
            existing.base_hp = stats.base_hp
            existing.base_atk = stats.base_atk
            existing.base_def = stats.base_def
            existing.base_spd = stats.base_spd
            existing.base_cr = stats.base_cr
            existing.base_cd = stats.base_cd
            existing.updated_at = datetime.utcnow()
        else:
            # 새로 생성
            new_monster = Monster(
                master_id=stats.master_id,
                name_ko=stats.name_ko,
                name_en=stats.name_en,
                element=stats.element,
                awakened=stats.awakened,
                nat_stars=stats.nat_stars,
                base_hp=stats.base_hp,
                base_atk=stats.base_atk,
                base_def=stats.base_def,
                base_spd=stats.base_spd,
                base_cr=stats.base_cr,
                base_cd=stats.base_cd,
            )
            session.add(new_monster)
        
        upserted += 1
    
    session.commit()
    print(f"Successfully upserted {upserted} monsters to database")


def export_monsters(output_path: str, db_url: str = "sqlite:///sw_mcp.db"):
    """DB에서 몬스터 데이터를 CSV로 export"""
    print(f"Exporting monsters from database to {output_path}...")
    
    session = get_session(db_url)
    monsters = session.query(Monster).order_by(Monster.master_id).all()
    
    if not monsters:
        print("Warning: No monsters found in database")
        return
    
    print(f"Found {len(monsters)} monsters in database")
    
    # CSV 작성
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'master_id', 'name_en', 'name_ko', 'element', 'awakened',
            'nat_stars', 'base_hp', 'base_atk', 'base_def', 'base_spd',
            'base_cr', 'base_cd'
        ])
        writer.writeheader()
        
        for monster in monsters:
            writer.writerow({
                'master_id': monster.master_id,
                'name_en': monster.name_en,
                'name_ko': monster.name_ko,
                'element': monster.element,
                'awakened': 'true' if monster.awakened else 'false',
                'nat_stars': monster.nat_stars,
                'base_hp': monster.base_hp,
                'base_atk': monster.base_atk,
                'base_def': monster.base_def,
                'base_spd': monster.base_spd,
                'base_cr': monster.base_cr,
                'base_cd': monster.base_cd,
            })
    
    print(f"Successfully exported {len(monsters)} monsters to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='SW-MCP 관리 커맨드')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # seed-monsters 커맨드
    seed_parser = subparsers.add_parser('seed-monsters', help='CSV에서 DB로 몬스터 데이터 seed')
    seed_parser.add_argument('csv_path', help='CSV 파일 경로')
    seed_parser.add_argument('--db-url', default='sqlite:///sw_mcp.db', help='데이터베이스 URL')
    
    # export-monsters 커맨드
    export_parser = subparsers.add_parser('export-monsters', help='DB에서 CSV로 몬스터 데이터 export')
    export_parser.add_argument('output_path', help='출력 CSV 파일 경로')
    export_parser.add_argument('--db-url', default='sqlite:///sw_mcp.db', help='데이터베이스 URL')
    
    # sync-remote 커맨드 (스텁)
    sync_parser = subparsers.add_parser('sync-remote', help='원격 공급자에서 동기화 (추후 구현)')
    sync_parser.add_argument('--provider', default='swarfarm', help='원격 공급자 이름')
    
    args = parser.parse_args()
    
    if args.command == 'seed-monsters':
        seed_monsters(args.csv_path, args.db_url)
    elif args.command == 'export-monsters':
        export_monsters(args.output_path, args.db_url)
    elif args.command == 'sync-remote':
        print(f"Remote sync with {args.provider} is not yet implemented")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

