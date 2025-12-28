"""HTTP client with retry, backoff, rate limiting, and conditional requests"""

import time
import random
from typing import Optional, Dict, Any
import httpx


class SwarfarmClient:
    """HTTP client for SWARFARM API with retry, backoff, rate limiting"""
    
    def __init__(
        self,
        base_url: str = "https://swarfarm.com/api/v2/",
        max_retries: int = 6,
        user_agent: str = "sw-mcp/1.0.0",
        rps: float = 2.0,  # requests per second
    ):
        """
        Args:
            base_url: API base URL
            max_retries: Maximum retry attempts
            user_agent: User-Agent header
            rps: Rate limit (requests per second)
        """
        self.base_url = base_url
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.rps = rps
        self.min_interval = 1.0 / rps if rps > 0 else 0
        self._last_request_time = 0.0
        
        self.client = httpx.Client(
            base_url=base_url,
            headers={"User-Agent": user_agent},
            timeout=30.0,
            follow_redirects=True,
        )
    
    def _rate_limit(self):
        """Rate limiting: ensure minimum interval between requests"""
        if self.min_interval > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_request_time = time.time()
    
    def _retry_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Retry logic with exponential backoff + jitter"""
        for attempt in range(self.max_retries):
            self._rate_limit()
            
            try:
                response = self.client.request(method, url, headers=headers, **kwargs)
                
                # Success
                if response.status_code < 400:
                    return response
                
                # 304 Not Modified is success (no body needed)
                if response.status_code == 304:
                    return response
                
                # 429 or 5xx: retry with backoff
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        backoff = (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(backoff)
                        continue
                
                # 4xx (except 429): don't retry
                response.raise_for_status()
                return response
                
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt < self.max_retries - 1:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff)
                    continue
                raise
        
        raise Exception(f"Request failed after {self.max_retries} attempts")
    
    def get(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> httpx.Response:
        """
        GET request with conditional headers
        
        Args:
            url: Request URL
            etag: If-None-Match header value
            last_modified: If-Modified-Since header value
        
        Returns:
            HTTP response (may be 304 Not Modified)
        """
        headers = {}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        
        return self._retry_request("GET", url, headers=headers)
    
    def close(self):
        """Close client"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


