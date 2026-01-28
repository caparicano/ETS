
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
from datetime import datetime

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.models import User, Organization, SectorType, Installation
from backend.infrastructure.seed_data import seed_initial_data

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_full.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user(db = None):
    # Mock user for Org 1
    return User(id=1, organization_id=1, email="boss@ceramica.pt", hashed_password="pw")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides["backend.infrastructure.auth.get_current_user"] = override_get_current_user

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_initial_data(db) # Seeds Inst 1, Streams, Tasks
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_full.db"):
        os.remove("./test_full.db")

def test_complete_year_cycle(db_session):
    """
    Simulate entire year for ceramic company.
    1. Check Tasks
    2. Analyze Fuel Switch (Strategy)
    3. Grant Verifier Access
    """
    
    # 1. Check Tasks
    resp = client.get("/api/v1/tasks?installation_id=1")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) > 0
    
    # 2. Strategic Analysis
    strat_resp = client.post("/api/v1/advisory/analyze-fuel-switch", json={
        "installation_id": 1,
        "from_fuel": "natural_gas",
        "to_fuel": "biomass"
    })
    assert strat_resp.status_code == 200
    data = strat_resp.json()
    assert "payback_period_years" in data
    assert "RED II" in data["regulatory_requirements"][0]
    
    # 3. Grant Verifier Access
    verifier_resp = client.post("/api/v1/verifier/grant-access", json={
        "installation_id": 1,
        "verifier_email": "auditor@apcer.pt",
        "expires_days": 15
    })
    assert verifier_resp.status_code == 200
    v_data = verifier_resp.json()
    token = v_data["access_token"]
    
    # 4. Verifier accesses Dashboard (No Auth needed, just token)
    # We remove the dependency override for this specific call or mock it? 
    # Actually verifier endpoint depends ONLY on get_db, not get_current_user for the dashboard view.
    dash_resp = client.get(f"/api/v1/verifier/dashboard/{token}")
    assert dash_resp.status_code == 200
    assert dash_resp.json()["installation_name"] == "Factory 1"
    
    print("\n✅ FULL CONSULTANT CYCLE PASSED")
