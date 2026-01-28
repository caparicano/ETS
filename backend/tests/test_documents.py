
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import os
import io

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.domain.document_types import APADocumentType

# Setup Test Database (SQLite for speed/isolation)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

def test_upload_valid_document(test_db):
    """Test uploading a valid PDF invoice"""
    
    # Create a dummy PDF file in memory
    file_content = b"%PDF-1.4 ... dummy content ..."
    file = io.BytesIO(file_content)
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invoice.pdf", file, "application/pdf")},
        data={
            "document_type": APADocumentType.FATURAS_GAS_NATURAL.value,
            "installation_id": 1,
            "reporting_year": 2024
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["version"] == 1
    assert data["filename"] == "invoice.pdf"

def test_upload_invalid_format(test_db):
    """Test that uploading a .exe file is rejected"""
    
    file_content = b"exe content"
    file = io.BytesIO(file_content)
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("virus.exe", file, "application/x-msdownload")},
        data={
            "document_type": APADocumentType.RELATORIO_EMISSOES.value,
            "installation_id": 1,
            "reporting_year": 2024
        }
    )
    
    assert response.status_code == 400
    assert "Formato inválido" in response.json()["detail"]

def test_document_versioning(test_db):
    """Test that uploading the same document type creates version 2"""
    
    file_content = b"updated content"
    file = io.BytesIO(file_content)
    
    # First upload was in test_upload_valid_document (v1)
    # This should be v2
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invoice_v2.pdf", file, "application/pdf")},
        data={
            "document_type": APADocumentType.FATURAS_GAS_NATURAL.value,
            "installation_id": 1,
            "reporting_year": 2024
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["version"] == 2
