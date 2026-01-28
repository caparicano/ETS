
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
from datetime import date

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.seed_data import seed_initial_data
from backend.infrastructure.models import SourceStream, User, EmissionEntry

# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_int.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user(db = None):
    # Mock user from seed data (Org 1)
    return User(id=1, organization_id=1, email="test@ceramets.com", hashed_password="pw")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides["backend.infrastructure.auth.get_current_user"] = override_get_current_user

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_initial_data(db)
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_int.db"):
        os.remove("./test_int.db")

def test_full_compliance_lifecycle(test_db):
    """
    INTEGRATION TEST #1: The Happy Path
    1. Fetch Form Definition for Ceramic Stream
    2. Submit Data
    3. Verify Calculation Persistence
    """
    
    # Step 1: Get Form Definition for Natural Gas
    # We find the specific stream seeded for ceramic
    stream = test_db.query(SourceStream).filter(SourceStream.name.like("Natural Gas%")).first()
    assert stream is not None, "Seeding failed for Natural Gas Stream"
    
    response = client.get(f"/api/v1/source-streams/{stream.id}/form-definition")
    assert response.status_code == 200
    form_def = response.json()
    
    assert "activity_data_nm3" in form_def["json_schema"]["properties"]
    
    # Step 2: Submit Data (POST)
    payload = {
        "source_stream_id": stream.id,
        "period_start": "2024-02-01",
        "period_end": "2024-02-29",
        "input_data": {
            "activity_data_nm3": 1000.0
        }
    }
    
    post_response = client.post("/api/v1/emission-entries", json=payload)
    assert post_response.status_code == 201
    entry_data = post_response.json()
    
    # 1000 * 0.03854 * 56.1 * 1.0 * 0.001 = 2.162094
    assert entry_data["calculated_tco2"] > 2.0
    entry_id = entry_data["id"]
    
    # Step 3: Verify Persistence
    db_entry = test_db.query(EmissionEntry).filter(EmissionEntry.id == entry_id).first()
    assert db_entry is not None
    assert db_entry.calculated_tco2 == entry_data["calculated_tco2"]

def test_access_denied_other_tenant(test_db):
    """
    INTEGRATION TEST #2: Tenancy Check
    """
    # Try accessing non-existent stream
    response = client.get("/api/v1/source-streams/999/form-definition")
    assert response.status_code == 404
