"""Test endpoint sync"""

import pytest
from unittest.mock import Mock, patch
from src.sw_mcp.swarfarm.client import SwarfarmClient
from src.sw_mcp.swarfarm.sync import sync_endpoint
from src.sw_mcp.db.repo import SwarfarmRepository
import tempfile
import os


@pytest.fixture
def temp_db():
    """Temporary database"""
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = db_file.name
    db_file.close()
    
    db_url = f"sqlite:///{db_path}"
    SwarfarmRepository.create_tables(db_url)
    
    yield db_url
    
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_list_response():
    """Mock paginated list response"""
    return {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200},
        ]
    }


def test_sync_endpoint_200(temp_db, mock_list_response):
    """Test sync with 200 response"""
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"ETag": "test-etag", "Last-Modified": "test-date"}
        mock_response.json.return_value = mock_list_response
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = SwarfarmClient(rps=0)
        repo = SwarfarmRepository()
        
        try:
            stats = sync_endpoint(
                client,
                repo,
                "test_endpoint",
                "https://example.com/api/v2/test/",
                verbose=False,
            )
            
            assert stats["inserted"] == 2
            assert stats["updated"] == 0
            assert stats["unchanged"] == 0
            assert stats["errors"] == 0
            assert not stats["is_304"]
            
            # Verify sync state
            state = repo.get_sync_state("test_endpoint")
            assert state is not None
            assert state.etag == "test-etag"
            assert state.last_modified == "test-date"
            assert state.last_count == 2
        finally:
            client.close()
            repo.close()


def test_sync_endpoint_304(temp_db):
    """Test sync with 304 Not Modified"""
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 304
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = SwarfarmClient(rps=0)
        repo = SwarfarmRepository()
        
        # Set up existing state
        repo.upsert_sync_state(
            "test_endpoint",
            "https://example.com/api/v2/test/",
            etag="existing-etag",
            last_modified="existing-date",
            success=True,
        )
        repo.commit()
        
        try:
            stats = sync_endpoint(
                client,
                repo,
                "test_endpoint",
                "https://example.com/api/v2/test/",
                verbose=False,
            )
            
            assert stats["is_304"]
            assert stats["inserted"] == 0
            assert stats["updated"] == 0
            assert stats["unchanged"] == 0
        finally:
            client.close()
            repo.close()

