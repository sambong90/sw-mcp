"""SWARFARM API v2 클라이언트"""

import time
import random
from typing import Iterator, Dict, Any, Optional
import httpx
from urllib.parse import urljoin


class SwarfarmClient:
    """SWARFARM API v2 클라이언트"""
    
    def __init__(
        self,
        base_url: str = "https://swarfarm.com/api/v2/",
        sleep_ms: int = 100,
        max_retries: int = 5,
        user_agent: str = "sw-mcp/1.0.0"
    ):
        """
        Args:
            base_url: SWARFARM API base URL
            sleep_ms: 요청 간 슬립 시간 (밀리초)
            max_retries: 최대 재시도 횟수
            user_agent: User-Agent 헤더
        """
        self.base_url = base_url
        self.sleep_ms = sleep_ms / 1000.0  # 초 단위로 변환
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.client = httpx.Client(
            base_url=base_url,
            headers={"User-Agent": user_agent},
            timeout=30.0
        )
    
    def _sleep(self):
        """요청 간 슬립"""
        if self.sleep_ms > 0:
            time.sleep(self.sleep_ms)
    
    def _retry_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """재시도 로직이 포함된 요청"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.request(method, url, **kwargs)
                
                # 성공
                if response.status_code < 400:
                    return response
                
                # 429 (Rate Limit) 또는 5xx 에러
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff with jitter
                        backoff = (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(backoff)
                        continue
                
                # 4xx 에러 (429 제외)는 재시도하지 않음
                response.raise_for_status()
                return response
                
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt < self.max_retries - 1:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(backoff)
                    continue
                raise
        
        raise Exception(f"Request failed after {self.max_retries} attempts")
    
    def get_monsters_all(self, max_pages: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """
        모든 몬스터를 pagination으로 가져오기 (generator)
        
        Args:
            max_pages: 최대 페이지 수 (디버그용, None이면 모두)
        
        Yields:
            몬스터 딕셔너리
        """
        url = "monsters/?format=json"
        page_count = 0
        
        while url:
            if max_pages and page_count >= max_pages:
                break
            
            self._sleep()
            
            try:
                response = self._retry_request("GET", url)
                data = response.json()
                
                # results 리스트에서 몬스터들을 yield
                results = data.get("results", [])
                for monster in results:
                    yield monster
                
                # 다음 페이지 URL
                url = data.get("next")
                if url:
                    # 절대 URL이면 그대로, 상대 URL이면 base_url과 결합
                    if not url.startswith("http"):
                        url = urljoin(self.base_url, url)
                
                page_count += 1
                
            except Exception as e:
                print(f"Error fetching page {url}: {e}")
                raise
    
    def get_monsters_list(self, max_pages: Optional[int] = None) -> list[Dict[str, Any]]:
        """
        모든 몬스터를 리스트로 반환
        
        Args:
            max_pages: 최대 페이지 수 (디버그용, None이면 모두)
        
        Returns:
            몬스터 딕셔너리 리스트
        """
        return list(self.get_monsters_all(max_pages=max_pages))
    
    def close(self):
        """클라이언트 종료"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


