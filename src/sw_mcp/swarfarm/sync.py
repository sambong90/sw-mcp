"""Sync logic for SWARFARM endpoints"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from urllib.parse import urljoin
from .client import SwarfarmClient
from .paginator import paginate_list
from .discovery import discover_endpoints
from ..db.repo import SwarfarmRepository


class SyncStats:
    """Statistics for sync operation"""
    def __init__(self):
        self.endpoints_total = 0
        self.endpoints_changed = 0
        self.endpoints_304 = 0
        self.objects_inserted = 0
        self.objects_updated = 0
        self.objects_unchanged = 0
        self.errors_total = 0
        self.endpoint_details: List[Dict[str, Any]] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "endpoints_total": self.endpoints_total,
            "endpoints_changed": self.endpoints_changed,
            "endpoints_304": self.endpoints_304,
            "objects_inserted": self.objects_inserted,
            "objects_updated": self.objects_updated,
            "objects_unchanged": self.objects_unchanged,
            "errors_total": self.errors_total,
            "endpoint_details": self.endpoint_details,
        }


def sync_endpoint(
    client: SwarfarmClient,
    repo: SwarfarmRepository,
    endpoint_name: str,
    endpoint_url: str,
    max_pages: Optional[int] = None,
    enable_changelog: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Sync a single endpoint
    
    Args:
        client: SwarfarmClient
        repo: SwarfarmRepository
        endpoint_name: Endpoint name
        endpoint_url: Endpoint URL
        max_pages: Max pages (debug)
        enable_changelog: Enable change logging
        verbose: Verbose output
    
    Returns:
        Stats dictionary
    """
    stats = {
        "endpoint": endpoint_name,
        "inserted": 0,
        "updated": 0,
        "unchanged": 0,
        "errors": 0,
        "is_304": False,
        "error_msg": None,
    }
    
    try:
        # Load sync state
        state = repo.get_sync_state(endpoint_name)
        etag = state.etag if state else None
        last_modified = state.last_modified if state else None
        
        # Make request with conditional headers
        response = client.get(endpoint_url, etag=etag, last_modified=last_modified)
        
        # 304 Not Modified
        if response.status_code == 304:
            stats["is_304"] = True
            repo.upsert_sync_state(
                endpoint_name,
                endpoint_url,
                etag=etag,
                last_modified=last_modified,
                success=True,
            )
            repo.commit()
            if verbose:
                print(f"  ✓ {endpoint_name}: 304 Not Modified (no changes)")
            return stats
        
        # 200 OK: process pagination
        response.raise_for_status()
        
        # Extract ETag/Last-Modified from response headers
        new_etag = response.headers.get("ETag")
        new_last_modified = response.headers.get("Last-Modified")
        
        # Parse first page to get pagination info
        data = response.json()
        list_url = endpoint_url
        
        # Iterate pagination
        item_count = 0
        for item in paginate_list(client, list_url, etag, last_modified, max_pages):
            item_count += 1
            
            # Extract object_id
            object_id = item.get("id")
            if object_id is None:
                stats["errors"] += 1
                if verbose:
                    print(f"    Warning: Item missing 'id' in {endpoint_name}")
                continue
            
            # Extract com2us_id if available
            com2us_id = item.get("com2us_id")
            
            # Construct source URL
            source_url = f"{endpoint_url}{object_id}/" if endpoint_url.endswith("/") else f"{endpoint_url}/{object_id}/"
            
            # Upsert
            try:
                _, is_insert, is_update = repo.upsert_raw(
                    endpoint_name,
                    object_id,
                    item,
                    source_url,
                    com2us_id=com2us_id,
                    enable_changelog=enable_changelog,
                )
                
                if is_insert:
                    stats["inserted"] += 1
                elif is_update:
                    stats["updated"] += 1
                else:
                    stats["unchanged"] += 1
            except Exception as e:
                stats["errors"] += 1
                if verbose:
                    print(f"    Error upserting {endpoint_name}/{object_id}: {e}")
        
        # Update sync state
        repo.upsert_sync_state(
            endpoint_name,
            endpoint_url,
            etag=new_etag,
            last_modified=new_last_modified,
            last_count=item_count,
            success=True,
        )
        repo.commit()
        
        if verbose:
            print(f"  ✓ {endpoint_name}: {stats['inserted']} inserted, {stats['updated']} updated, {stats['unchanged']} unchanged, {stats['errors']} errors")
    
    except Exception as e:
        stats["errors"] += 1
        stats["error_msg"] = str(e)
        repo.upsert_sync_state(
            endpoint_name,
            endpoint_url,
            last_error=str(e),
            success=False,
        )
        repo.rollback()
        if verbose:
            print(f"  ✗ {endpoint_name}: Error - {e}")
    
    return stats


def sync_all(
    client: SwarfarmClient,
    repo: SwarfarmRepository,
    max_pages: Optional[int] = None,
    enable_changelog: bool = True,
    verbose: bool = True,
) -> SyncStats:
    """
    Discover and sync all endpoints
    
    Args:
        client: SwarfarmClient
        repo: SwarfarmRepository
        max_pages: Max pages per endpoint (debug)
        enable_changelog: Enable change logging
        verbose: Verbose output
    
    Returns:
        SyncStats object
    """
    stats = SyncStats()
    
    if verbose:
        print(f"[{datetime.now()}] Starting SWARFARM sync...")
        print(f"  Discovering endpoints...")
    
    # Discover endpoints
    try:
        endpoints = discover_endpoints(client)
        stats.endpoints_total = len(endpoints)
        
        if verbose:
            print(f"  Found {len(endpoints)} endpoints")
            print()
    except Exception as e:
        if verbose:
            print(f"  ✗ Discovery failed: {e}")
        stats.errors_total += 1
        return stats
    
    # Create snapshot
    snapshot = repo.create_snapshot()
    
    # Sync each endpoint
    for endpoint_name, endpoint_url in endpoints:
        endpoint_stats = sync_endpoint(
            client,
            repo,
            endpoint_name,
            endpoint_url,
            max_pages=max_pages,
            enable_changelog=enable_changelog,
            verbose=verbose,
        )
        
        stats.endpoint_details.append(endpoint_stats)
        
        if endpoint_stats["is_304"]:
            stats.endpoints_304 += 1
        elif endpoint_stats["inserted"] > 0 or endpoint_stats["updated"] > 0:
            stats.endpoints_changed += 1
        
        stats.objects_inserted += endpoint_stats["inserted"]
        stats.objects_updated += endpoint_stats["updated"]
        stats.objects_unchanged += endpoint_stats["unchanged"]
        stats.errors_total += endpoint_stats["errors"]
    
    # Update snapshot
    repo.update_snapshot(snapshot, stats.to_dict())
    repo.commit()
    
    if verbose:
        print()
        print(f"[{datetime.now()}] Sync completed!")
        print(f"  Endpoints: {stats.endpoints_total} total, {stats.endpoints_changed} changed, {stats.endpoints_304} unchanged (304)")
        print(f"  Objects: {stats.objects_inserted} inserted, {stats.objects_updated} updated, {stats.objects_unchanged} unchanged")
        print(f"  Errors: {stats.errors_total}")
    
    return stats

