"""Test endpoint discovery"""

import pytest
from unittest.mock import Mock, patch
from src.sw_mcp.swarfarm.discovery import discover_endpoints
from src.sw_mcp.swarfarm.client import SwarfarmClient


@pytest.fixture
def mock_root_response():
    """Mock API root response"""
    return {
        "monsters": "https://swarfarm.com/api/v2/monsters/",
        "skills": "https://swarfarm.com/api/v2/skills/",
        "runes": "https://swarfarm.com/api/v2/runes/",
    }


def test_discover_endpoints(mock_root_response):
    """Test endpoint discovery"""
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_root_response
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = SwarfarmClient(rps=0)  # No rate limit for test
        
        endpoints = discover_endpoints(client)
        
        assert len(endpoints) == 3
        assert ("monsters", "https://swarfarm.com/api/v2/monsters/") in endpoints
        assert ("skills", "https://swarfarm.com/api/v2/skills/") in endpoints
        assert ("runes", "https://swarfarm.com/api/v2/runes/") in endpoints
        
        client.close()


