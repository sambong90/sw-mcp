"""API endpoint tests"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.sw_api.main import app
from src.sw_api.database import Base, get_db

# Test database (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_swex_json():
    """Sample SWEX JSON for testing"""
    return {
        "runes": [
            {
                "rune_id": 100,
                "slot_no": 1,
                "set_id": 5,  # Rage
                "pri_eff": [4, 63],  # ATK%
                "sec_eff": [[9, 20, 0, 0]],  # CR 20
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            },
            {
                "rune_id": 200,
                "slot_no": 2,
                "set_id": 5,  # Rage
                "pri_eff": [4, 63],  # ATK%
                "sec_eff": [[9, 15, 0, 0]],  # CR 15
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            },
            {
                "rune_id": 300,
                "slot_no": 3,
                "set_id": 5,  # Rage
                "pri_eff": [1, 1000],  # HP
                "sec_eff": [[9, 20, 0, 0]],  # CR 20
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            },
            {
                "rune_id": 400,
                "slot_no": 4,
                "set_id": 5,  # Rage
                "pri_eff": [10, 80],  # CD
                "sec_eff": [[9, 20, 0, 0]],  # CR 20
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            },
            {
                "rune_id": 500,
                "slot_no": 5,
                "set_id": 4,  # Blade
                "pri_eff": [1, 1000],  # HP
                "sec_eff": [[9, 20, 0, 0]],  # CR 20
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            },
            {
                "rune_id": 600,
                "slot_no": 6,
                "set_id": 4,  # Blade
                "pri_eff": [4, 63],  # ATK%
                "sec_eff": [[9, 20, 0, 0]],  # CR 20
                "class": 6,
                "rank": 5,
                "prefix_eff": 0
            }
        ],
        "unit_list": []
    }


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "SW-MCP API"


def test_create_import(client, sample_swex_json, tmp_path):
    """Test creating an import"""
    import json
    import tempfile
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_swex_json, f)
        temp_file = f.name
    
    try:
        with open(temp_file, "rb") as f:
            response = client.post(
                "/imports",
                files={"file": ("test.json", f, "application/json")}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "rune_count" in data
        assert data["rune_count"] == 6
        assert "created_at" in data
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_get_import(client, sample_swex_json, tmp_path):
    """Test getting an import"""
    import json
    import tempfile
    
    # Create import first
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_swex_json, f)
        temp_file = f.name
    
    try:
        with open(temp_file, "rb") as f:
            create_response = client.post(
                "/imports",
                files={"file": ("test.json", f, "application/json")}
            )
        
        import_id = create_response.json()["id"]
        
        # Get import
        response = client.get(f"/imports/{import_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == import_id
        assert data["rune_count"] == 6
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_create_search_job(client, sample_swex_json, tmp_path):
    """Test creating a search job"""
    import json
    import tempfile
    
    # Create import first
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_swex_json, f)
        temp_file = f.name
    
    try:
        with open(temp_file, "rb") as f:
            create_response = client.post(
                "/imports",
                files={"file": ("test.json", f, "application/json")}
            )
        
        import_id = create_response.json()["id"]
        
        # Create search job
        job_data = {
            "import_id": import_id,
            "params": {
                "target": "A",
                "mode": "exhaustive",
                "top_n": 10
            }
        }
        
        response = client.post("/search-jobs", json=job_data)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["import_id"] == import_id
        assert data["status"] == "pending"
        assert data["progress"] == 0.0
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_get_search_job(client, sample_swex_json, tmp_path):
    """Test getting a search job"""
    import json
    import tempfile
    
    # Create import and job
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_swex_json, f)
        temp_file = f.name
    
    try:
        with open(temp_file, "rb") as f:
            create_response = client.post(
                "/imports",
                files={"file": ("test.json", f, "application/json")}
            )
        
        import_id = create_response.json()["id"]
        
        job_data = {
            "import_id": import_id,
            "params": {"target": "A", "mode": "exhaustive", "top_n": 10}
        }
        
        create_job_response = client.post("/search-jobs", json=job_data)
        job_id = create_job_response.json()["id"]
        
        # Get job
        response = client.get(f"/search-jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["status"] == "pending"
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_get_search_results_not_completed(client, sample_swex_json, tmp_path):
    """Test getting results for non-completed job"""
    import json
    import tempfile
    
    # Create import and job
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_swex_json, f)
        temp_file = f.name
    
    try:
        with open(temp_file, "rb") as f:
            create_response = client.post(
                "/imports",
                files={"file": ("test.json", f, "application/json")}
            )
        
        import_id = create_response.json()["id"]
        
        job_data = {
            "import_id": import_id,
            "params": {"target": "A", "mode": "exhaustive", "top_n": 10}
        }
        
        create_job_response = client.post("/search-jobs", json=job_data)
        job_id = create_job_response.json()["id"]
        
        # Try to get results (should fail - job not completed)
        response = client.get(f"/search-jobs/{job_id}/results")
        assert response.status_code == 400
    finally:
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)

