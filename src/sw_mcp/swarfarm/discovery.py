"""Discover endpoints from SWARFARM API root"""

from typing import List, Tuple, Dict, Any
from .client import SwarfarmClient


def discover_endpoints(client: SwarfarmClient) -> List[Tuple[str, str]]:
    """
    Discover all endpoints from API root
    
    Args:
        client: SwarfarmClient instance
    
    Returns:
        List of (endpoint_name, endpoint_url) tuples
    
    Example:
        [("monsters", "https://swarfarm.com/api/v2/monsters/"), ...]
    """
    response = client.get("")
    response.raise_for_status()
    root_data = response.json()
    
    endpoints = []
    base_url = client.base_url.rstrip("/")
    
    # Root JSON keys are endpoint names, values are URLs
    for key, value in root_data.items():
        if isinstance(value, str) and value.startswith("http"):
            # Extract endpoint name from key or URL
            endpoint_name = key
            endpoint_url = value.rstrip("/") + "/"
            endpoints.append((endpoint_name, endpoint_url))
        elif isinstance(value, str) and value.startswith("/"):
            # Relative URL
            endpoint_name = key
            endpoint_url = base_url + value.rstrip("/") + "/"
            endpoints.append((endpoint_name, endpoint_url))
    
    return endpoints

