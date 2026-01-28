
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
from datetime import date

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.seed_data import seed_initial_data
from backend.infrastructure.models import SourceStream, User

# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_comp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock Auth to return the seeded user
def override_get_current_user(db = None):
    # Retrieve the user created in seed_data (via org creation) 
    # Actually seed_data doesn't create a user, so we need to ensure one exists or mock the object
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
    if os.path.exists("./test_comp.db"):
        os.remove("./test_comp.db")

def test_get_form_definition(test_db):
    """Verify we can fetch the JSON Schema for the Natural Gas stream."""
    stream = test_db.query(SourceStream).filter_by(name="Natural Gas Combustion Line 1").first()
    assert stream is not None
    
    response = client.get(f"/api/v1/source-streams/{stream.id}/form-definition")
    assert response.status_code == 200
    data = response.json()
    
    assert data["source_stream_name"] == stream.name
    assert "activity_data" in data["json_schema"]["properties"]
    assert data["json_schema"]["properties"]["activity_data"]["unit"] == "Nm³"

def test_submit_emission_entry(test_db):
    """Verify that submitting data triggers the calc engine and saves the result."""
    stream = test_db.query(SourceStream).filter_by(name="Natural Gas Combustion Line 1").first()
    
    payload = {
        "source_stream_id": stream.id,
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "input_data": {
            "activity_data": 50000.0
        }
    }
    
    response = client.post("/api/v1/emission-entries", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    
    # Validation: 50000 * 0.03854 * 56.1 * 1.0 * 0.001 ≈ 108.1047
    assert data["calculated_tco2"] == 108.1047
    assert data["calculation_trace"]["factors_snapshot"]["ef"] == 56.1
    assert "activity_data" in data["calculation_trace"]["inputs_snapshot"]
