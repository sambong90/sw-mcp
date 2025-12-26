"""Pagination generator for SWARFARM list endpoints"""

from typing import Iterator, Dict, Any, Optional
from urllib.parse import urljoin
from .client import SwarfarmClient


def paginate_list(
    client: SwarfarmClient,
    list_url: str,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Paginate through a list endpoint
    
    Args:
        client: SwarfarmClient instance
        list_url: Initial list URL
        etag: If-None-Match header value
        last_modified: If-Modified-Since header value
        max_pages: Maximum pages to fetch (debug, None = all)
    
    Yields:
        Item dictionaries from results
    """
    url = list_url
    page_count = 0
    
    while url:
        if max_pages and page_count >= max_pages:
            break
        
        response = client.get(url, etag=etag, last_modified=last_modified)
        
        # 304 Not Modified: no changes, skip pagination
        if response.status_code == 304:
            return  # Generator exits
        
        response.raise_for_status()
        data = response.json()
        
        # Yield items from results
        results = data.get("results", [])
        for item in results:
            yield item
        
        # Next page URL
        url = data.get("next")
        if url:
            # Convert relative URL to absolute
            if not url.startswith("http"):
                url = urljoin(client.base_url, url)
        
        # Only use conditional headers on first request
        etag = None
        last_modified = None
        
        page_count += 1

