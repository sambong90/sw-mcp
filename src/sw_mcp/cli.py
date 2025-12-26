"""CLI for SWARFARM ingestion"""

import sys
import argparse
import os
from .swarfarm.client import SwarfarmClient
from .swarfarm.discovery import discover_endpoints
from .swarfarm.sync import sync_all, sync_endpoint
from .db.repo import SwarfarmRepository
from .db.engine import DB_URL


def cmd_discover(args):
    """Discover endpoints"""
    rps = float(args.rps) if args.rps else 2.0
    client = SwarfarmClient(rps=rps)
    
    try:
        endpoints = discover_endpoints(client)
        print(f"Discovered {len(endpoints)} endpoints:")
        for name, url in endpoints:
            print(f"  - {name}: {url}")
    finally:
        client.close()


def cmd_sync(args):
    """Sync endpoints"""
    db_url = args.db_url or os.getenv("SW_MCP_DB_URL", DB_URL)
    rps = float(args.rps) if args.rps else 2.0
    enable_changelog = not args.no_changelog
    
    # Create tables if needed
    SwarfarmRepository.create_tables(db_url)
    
    client = SwarfarmClient(rps=rps)
    repo = SwarfarmRepository()
    
    try:
        if args.all:
            # Sync all
            stats = sync_all(
                client,
                repo,
                max_pages=args.max_pages,
                enable_changelog=enable_changelog,
                verbose=True,
            )
            
            # Print summary
            print()
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Endpoints: {stats.endpoints_total} total")
            print(f"  - Changed: {stats.endpoints_changed}")
            print(f"  - Unchanged (304): {stats.endpoints_304}")
            print(f"Objects:")
            print(f"  - Inserted: {stats.objects_inserted}")
            print(f"  - Updated: {stats.objects_updated}")
            print(f"  - Unchanged: {stats.objects_unchanged}")
            print(f"Errors: {stats.errors_total}")
        
        elif args.endpoint:
            # Sync single endpoint
            # Discover to get URL
            endpoints = discover_endpoints(client)
            endpoint_dict = dict(endpoints)
            
            if args.endpoint not in endpoint_dict:
                print(f"Error: Endpoint '{args.endpoint}' not found")
                print(f"Available endpoints: {', '.join(endpoint_dict.keys())}")
                sys.exit(1)
            
            endpoint_url = endpoint_dict[args.endpoint]
            stats = sync_endpoint(
                client,
                repo,
                args.endpoint,
                endpoint_url,
                max_pages=args.max_pages,
                enable_changelog=enable_changelog,
                verbose=True,
            )
            
            print()
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Endpoint: {args.endpoint}")
            if stats["is_304"]:
                print("Status: 304 Not Modified (no changes)")
            else:
                print(f"Inserted: {stats['inserted']}")
                print(f"Updated: {stats['updated']}")
                print(f"Unchanged: {stats['unchanged']}")
                print(f"Errors: {stats['errors']}")
        else:
            print("Error: Must specify --all or --endpoint")
            sys.exit(1)
    
    finally:
        client.close()
        repo.close()


def main():
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(description="SWARFARM API v2 ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Discover command
    discover_parser = subparsers.add_parser("swarfarm-discover", help="Discover endpoints")
    discover_parser.add_argument("--rps", type=float, help="Rate limit (requests per second)")
    
    # Sync command
    sync_parser = subparsers.add_parser("swarfarm-sync", help="Sync endpoints")
    sync_parser.add_argument("--all", action="store_true", help="Sync all endpoints")
    sync_parser.add_argument("--endpoint", type=str, help="Sync single endpoint")
    sync_parser.add_argument("--db-url", type=str, help=f"DB URL (default: {DB_URL})")
    sync_parser.add_argument("--rps", type=float, help="Rate limit (requests per second)")
    sync_parser.add_argument("--max-pages", type=int, help="Max pages per endpoint (debug)")
    sync_parser.add_argument("--no-changelog", action="store_true", help="Disable change logging")
    
    args = parser.parse_args()
    
    if args.command == "swarfarm-discover":
        cmd_discover(args)
    elif args.command == "swarfarm-sync":
        cmd_sync(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

