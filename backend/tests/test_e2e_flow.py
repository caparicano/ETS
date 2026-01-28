
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
import json
from datetime import date

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.models import User, Organization, SectorType, Installation, SourceStream
from backend.domain.wizard_service import WizardService, WizardState

# Setup Isolated Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Mock Auth User
def override_get_current_user(db = None):
    return User(id=1, organization_id=1, email="manager@ceramica.pt", hashed_password="pw")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides["backend.infrastructure.auth.get_current_user"] = override_get_current_user

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed minimal Org
    org = Organization(id=1, name="Ceramica E2E", vat_number="PT999", sector=SectorType.CERAMIC)
    db.add(org)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_e2e.db"):
        os.remove("./test_e2e.db")

def test_complete_onboarding_lifecycle(db_session):
    """
    CRITICAL E2E TEST:
    1. Start Wizard (Upload PDF)
    2. Approve AI Config
    3. Verify Assets Created (SourceStream, Factors, Tasks)
    4. Submit Monthly Data using generated config
    5. Verify Calculation
    """
    
    # --- STEP 1: Start Wizard (Mock Upload) ---
    # We bypass the file upload route logic slightly by using the service directly or mocking the parser response
    # to avoid needing a real PDF in the test suite.
    svc = WizardService(db_session)
    session = svc.create_session(organization_id=1)
    
    # Inject Mock Context (Simulate "After parsing & Interview")
    session.state = WizardState.PREVIEW_CONFIG
    session.context = {
        "parsed_permit": {"installation_name": "E2E Factory", "permit_id": "TEGEH-E2E"},
        "fuel_details": {"Kiln 1": "Natural Gas"},
        "generated_config": {
            "installation_name": "E2E Factory",
            "permit_id": "TEGEH-E2E",
            "streams": [
                {
                    "name": "Kiln 1 (Combustion)",
                    "fuel": "natural_gas",
                    "tier": 2,
                    "formula": "activity_data * ncv * ef * of * 0.001",
                    "inputs": ["activity_data"],
                    "json_schema": {
                        "type": "object", 
                        "properties": {"activity_data": {"type": "number", "unit": "Nm3"}},
                        "required": ["activity_data"]
                    },
                    "factors": [
                        {"name": "ncv", "value": 0.038, "unit": "GJ/Nm3"},
                        {"name": "ef", "value": 56.1, "unit": "kgCO2/GJ"},
                        {"name": "of", "value": 1.0, "unit": "fraction"}
                    ]
                }
            ]
        }
    }
    db_session.commit()
    
    # --- STEP 2: Approve Config (Via API) ---
    response = client.post(f"/api/v1/wizard/{session.id}/approve")
    assert response.status_code == 200
    installation_id = response.json()["installation_id"]
    
    # --- STEP 3: Verify Assets ---
    inst = db_session.query(Installation).get(installation_id)
    assert inst.name == "E2E Factory"
    assert len(inst.source_streams) == 1
    assert len(inst.tasks) > 0 # Should trigger Task Generation
    
    stream = inst.source_streams[0]
    assert stream.name == "Kiln 1 (Combustion)"
    assert stream.formula_template == "activity_data * ncv * ef * of * 0.001"
    
    # --- STEP 4: Submit Data (Using the created Stream) ---
    payload = {
        "source_stream_id": stream.id,
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "input_data": {
            "activity_data": 10000.0
        }
    }
    
    calc_response = client.post("/api/v1/emission-entries", json=payload)
    assert calc_response.status_code == 201
    calc_data = calc_response.json()
    
    # --- STEP 5: Verify Calculation ---
    # 10,000 * 0.038 * 56.1 * 1.0 * 0.001 = 21.318
    expected_val = 21.318
    assert abs(calc_data["calculated_tco2"] - expected_val) < 0.001
    
    print("\n✅ E2E TEST PASSED: Wizard Config -> Calculation Engine Handover successful!")
