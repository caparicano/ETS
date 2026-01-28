
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timedelta
import os
import io
from unittest.mock import MagicMock, patch

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.models import (
    User, Organization, SectorType, Installation, 
    SourceStream, EmissionFactor, Document, TaskStatus
)
from backend.infrastructure.seed_data import seed_initial_data
from backend.domain.apa_workflow import APAWorkflowService, APADocumentType

# --- DB Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_hardening.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Dynamic user override for security tests
current_user_mock = None

def override_get_current_user():
    return current_user_mock

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides["backend.infrastructure.auth.get_current_user"] = override_get_current_user

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    # 1. Create DB and Tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # 2. Seed Initial Data (Org 1, Inst 1, Streams, Tasks)
    seed_initial_data(db)
    
    # 3. Create Org 2 for isolation tests (The Intruder)
    org2 = Organization(name="Intruder Corp", vat_number="PT000000000", sector=SectorType.CERAMIC)
    db.add(org2)
    db.commit()
    user2 = User(email="spy@intruder.com", hashed_password="pw", organization_id=org2.id)
    db.add(user2)
    db.commit()
    
    yield db
    
    # 4. Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_hardening.db"):
        os.remove("./test_hardening.db")

@pytest.fixture(autouse=True)
def run_around_tests(db_session):
    # Reset current user to default (Org 1 Admin) before each test
    global current_user_mock
    current_user_mock = db_session.query(User).get(1)
    if not current_user_mock:
        # Fallback if seed ID 1 assumes something specific
        current_user_mock = User(id=1, organization_id=1, email="test@ceramets.com", hashed_password="pw")
    yield

# --- 1. Full Data Entry Cycle ---
def test_complete_emission_entry_workflow(db_session):
    start_time = datetime.now()
    
    # Get Stream (Seeded "Natural Gas Combustion - Tunnel Kiln")
    stream = db_session.query(SourceStream).filter(SourceStream.installation_id == 1).first()
    
    # Get Form Definition
    resp = client.get(f"/api/v1/source-streams/{stream.id}/form-definition")
    assert resp.status_code == 200
    
    # Submit Data (Jan 2024)
    payload = {
        "source_stream_id": stream.id,
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "input_data": {"activity_data_nm3": 1000.0}
    }
    resp = client.post("/api/v1/emission-entries", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    
    # Verify Calculation: 1000 * 0.03854 (NCV) * 56.1 (EF) * 1.0 (OF) * 0.001 = 2.162094
    # Note: Seed data uses specific names in formula_template
    assert data["calculated_tco2"] > 2.16
    assert data["calculated_tco2"] < 2.17
    
    # Assert Performance
    duration = (datetime.now() - start_time).total_seconds()
    assert duration < 2.0, "API response too slow"

# --- 2. Task Workflow ---
def test_task_generation_and_completion(db_session):
    # Trigger generation for current year
    resp = client.get("/api/v1/tasks?installation_id=1&year=2024")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) > 0
    
    # Pick pending task
    pending = next((t for t in tasks if t["status"] == "PENDING"), None)
    if pending:
        # Complete it
        resp = client.post(f"/api/v1/tasks/{pending['id']}/complete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETED"

# --- 3. Security / Isolation ---
def test_data_isolation_between_organizations(db_session):
    # Switch to User 2 (Org 2)
    global current_user_mock
    user2 = db_session.query(User).filter_by(email="spy@intruder.com").first()
    current_user_mock = user2
    
    # Try to access Org 1's tasks (Installation 1)
    resp = client.get("/api/v1/tasks?installation_id=1")
    
    # Expect 403 Forbidden
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

# --- 4. Historical Validity (Time Travel) ---
def test_emission_factor_temporal_validity(db_session):
    # Add an old Emission Factor valid only in the past (2020-2023)
    inst_id = 1
    stream = db_session.query(SourceStream).filter_by(installation_id=inst_id).first()
    
    old_ef = EmissionFactor(
        installation_id=inst_id,
        fuel_type="natural_gas",
        parameter_name="ef_kg_co2_gj", # Matches seed naming
        value=50.0, # Different from current 56.1
        unit="kg/GJ",
        tier=1,
        valid_from=datetime(2020,1,1),
        valid_to=datetime(2023,12,31),
        source="Old MRR"
    )
    db_session.add(old_ef)
    db_session.commit()
    
    # Submit for 2023 -> Should pick 50.0
    payload_2023 = {
        "source_stream_id": stream.id,
        "period_start": "2023-06-01",
        "period_end": "2023-06-30",
        "input_data": {"activity_data_nm3": 1000.0}
    }
    resp = client.post("/api/v1/emission-entries", json=payload_2023)
    assert resp.status_code == 201
    trace_2023 = resp.json()["calculation_trace"]
    # Check if 'ef_kg_co2_gj' used was 50.0
    assert trace_2023["factors_snapshot"]["ef_kg_co2_gj"] == 50.0
    
    # Submit for 2024 -> Should pick 56.1 (Current seed)
    payload_2024 = {
        "source_stream_id": stream.id,
        "period_start": "2024-06-01",
        "period_end": "2024-06-30",
        "input_data": {"activity_data_nm3": 1000.0}
    }
    resp = client.post("/api/v1/emission-entries", json=payload_2024)
    trace_2024 = resp.json()["calculation_trace"]
    assert trace_2024["factors_snapshot"]["ef_kg_co2_gj"] == 56.1

# --- 5. Document Rules ---
def test_document_validation_rules(db_session):
    # Invalid File Type (EXE)
    file_content = b"malicious content"
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("virus.exe", io.BytesIO(file_content), "application/x-msdownload")},
        data={"document_type": "faturas_gas_natural", "installation_id": 1, "reporting_year": 2024}
    )
    assert resp.status_code == 400
    # Validate Portuguese Error
    assert "Formato inválido" in resp.json()["detail"]
    
    # Valid PDF
    pdf_content = b"%PDF-1.4..."
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invoice.pdf", io.BytesIO(pdf_content), "application/pdf")},
        data={"document_type": "faturas_gas_natural", "installation_id": 1, "reporting_year": 2024}
    )
    assert resp.status_code == 201

# --- 6. APA Readiness ---
def test_apa_submission_readiness(db_session):
    # Use Domain Service directly
    svc = APAWorkflowService(db_session)
    
    # Check readiness for RE (Annual Report)
    result = svc.check_submission_readiness(1, 2024, APADocumentType.RELATORIO_EMISSOES)
    
    # Expect Not Ready because we haven't uploaded Verification Opinion
    assert result["ready"] is False
    assert "missing_documents" in result
    # We expect 'Parecer de Verificação' to be listed as missing
    assert any("Parecer" in d for d in result["missing_documents"])

# --- 7. Verifier Portal ---
def test_verifier_portal_access(db_session):
    # 1. Grant Access
    resp = client.post("/api/v1/verifier/grant-access", json={
        "installation_id": 1,
        "verifier_email": "audit@sgs.com",
        "expires_days": 1
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    
    # 2. Access Dashboard (No auth required for verifier, just token)
    resp = client.get(f"/api/v1/verifier/dashboard/{token}")
    assert resp.status_code == 200
    assert resp.json()["installation_name"] == "Factory 1"
    
    # 3. Invalid Token
    resp = client.get("/api/v1/verifier/dashboard/INVALID_TOKEN")
    assert resp.status_code == 403

# --- 8. AI Citations ---
@patch("backend.domain.rag_service.RAGService.ask")
def test_regulatory_citation_completeness(mock_ask, db_session):
    # Mock RAG response to avoid calling real Gemini API
    mock_ask.return_value = {
        "answer": "Biomass is zero-rated under RED II.",
        "citations": [
            {"doc": "MRR", "article": "Art 38", "snippet": "...", "relevance": 0.9}
        ]
    }
    
    resp = client.post("/api/v1/advisory/chat", json={
        "query": "Is biomass free?",
        "installation_id": 1
    })
    
    assert resp.status_code == 200
    data = resp.json()
    assert "citations" in data
    assert len(data["citations"]) > 0
    assert data["citations"][0]["doc"] == "MRR"
