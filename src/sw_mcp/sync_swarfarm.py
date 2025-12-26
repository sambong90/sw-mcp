"""SWARFARM 동기화 커맨드"""

import sys
import argparse
import time
from datetime import datetime
from .swarfarm_client import SwarfarmClient
from .db.repo import MonsterRepository
from .db.engine import DB_URL


def sync_monsters(
    db_url: str = None,
    sleep_ms: int = 100,
    max_pages: int = None,
    verbose: bool = True
):
    """
    몬스터 데이터 동기화
    
    Args:
        db_url: DB URL (None이면 환경변수/기본값)
        sleep_ms: 요청 간 슬립 시간 (밀리초)
        max_pages: 최대 페이지 수 (디버그용, None이면 모두)
        verbose: 상세 출력 여부
    """
    start_time = time.time()
    
    if verbose:
        print(f"[{datetime.now()}] Starting SWARFARM sync...")
        print(f"  DB URL: {db_url or DB_URL}")
        print(f"  Sleep: {sleep_ms}ms")
        if max_pages:
            print(f"  Max pages: {max_pages}")
        print()
    
    # 테이블 생성
    MonsterRepository.create_tables(db_url)
    
    # 클라이언트 및 레포지토리 초기화
    client = SwarfarmClient(sleep_ms=sleep_ms)
    repo = MonsterRepository()
    
    try:
        total_count = 0
        insert_count = 0
        update_count = 0
        error_count = 0
        
        # 페이지 단위로 받아서 즉시 upsert (streaming)
        for monster_data in client.get_monsters_all(max_pages=max_pages):
            total_count += 1
            
            try:
                # com2us_id 확인
                com2us_id = monster_data.get("com2us_id")
                if com2us_id is None:
                    if verbose:
                        print(f"  Warning: Skipping monster without com2us_id: {monster_data.get('name', 'Unknown')}")
                    error_count += 1
                    continue
                
                # 기존 레코드 확인
                existing = repo.get_by_com2us_id(com2us_id)
                is_update = existing is not None
                
                # Upsert
                repo.upsert(monster_data)
                
                if is_update:
                    update_count += 1
                else:
                    insert_count += 1
                
                # 주기적으로 커밋 (메모리 관리)
                if total_count % 100 == 0:
                    try:
                        repo.commit()
                        if verbose:
                            print(f"  Progress: {total_count} processed ({insert_count} inserted, {update_count} updated)")
                    except Exception as e:
                        repo.session.rollback()
                        if verbose:
                            print(f"  Error committing batch: {e}")
                        raise
                
            except ValueError as e:
                # 예상된 에러 (Crystal 등, 기본 스탯 없는 몬스터)
                error_count += 1
                if verbose and "no base stats" in str(e).lower():
                    # Crystal 등은 조용히 스킵
                    pass
                elif verbose:
                    print(f"  Skipping {monster_data.get('name', 'Unknown')}: {e}")
                continue
            except Exception as e:
                # 예상치 못한 에러
                error_count += 1
                repo.session.rollback()  # 에러 발생 시 rollback
                if verbose:
                    print(f"  Error processing monster {monster_data.get('name', 'Unknown')}: {e}")
                continue
        
        # 최종 커밋
        try:
            repo.commit()
        except Exception as e:
            repo.session.rollback()
            if verbose:
                print(f"  Error in final commit: {e}")
            raise
        
        elapsed = time.time() - start_time
        
        if verbose:
            print()
            print(f"[{datetime.now()}] Sync completed!")
            print(f"  Total processed: {total_count}")
            print(f"  Inserted: {insert_count}")
            print(f"  Updated: {update_count}")
            print(f"  Errors: {error_count}")
            print(f"  Elapsed time: {elapsed:.2f}s")
    
    finally:
        client.close()
        repo.close()


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="SWARFARM 몬스터 데이터 동기화")
    parser.add_argument(
        "resource",
        choices=["monsters"],
        help="동기화할 리소스 (현재는 monsters만 지원)"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=f"DB URL (기본값: {DB_URL})"
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=100,
        help="요청 간 슬립 시간 (밀리초, 기본값: 100)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="최대 페이지 수 (디버그용)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="상세 출력 비활성화"
    )
    
    args = parser.parse_args()
    
    if args.resource == "monsters":
        sync_monsters(
            db_url=args.db,
            sleep_ms=args.sleep_ms,
            max_pages=args.max_pages,
            verbose=not args.quiet
        )
    else:
        print(f"Unknown resource: {args.resource}")
        sys.exit(1)


if __name__ == "__main__":
    main()

