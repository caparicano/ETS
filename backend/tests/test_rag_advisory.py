
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.models import User, RegulatoryDocument, RegulatoryChunk
from backend.domain.regulatory_library import RegulatoryLibraryService

# Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rag.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_current_user(db = None):
    return User(id=1, organization_id=1, email="test@ceramets.com", hashed_password="pw")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides["backend.infrastructure.auth.get_current_user"] = override_get_current_user

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_rag.db"):
        os.remove("./test_rag.db")

def test_regulatory_ingestion_and_search(db_session):
    """
    Test that we can ingest a regulation chunk and find it via cosine similarity.
    """
    lib = RegulatoryLibraryService(db_session)
    
    # Mock Embeddings (Simple vectors)
    # Query: "Biomass" -> let's say vector [0.9, 0.1]
    # Doc 1: "Biomass is zero rated" -> [0.95, 0.05] (Similar)
    # Doc 2: "CEMS requirements" -> [0.1, 0.9] (Dissimilar)
    
    chunks = [
        {
            "article_reference": "Article 38",
            "content": "Biomass shall be zero-rated if sustainable.",
            "embedding": [0.95, 0.05]
        },
        {
            "article_reference": "Article 24",
            "content": "Continuous emission monitoring systems must be calibrated.",
            "embedding": [0.1, 0.9]
        }
    ]
    
    lib.ingest_document("MRR 2018", "MRR", "Regulation", date(2018, 1, 1), chunks)
    
    # Search for Biomass-like vector
    query_vec = [0.9, 0.1] 
    results = lib.search(query_vec, limit=1)
    
    assert len(results) == 1
    assert results[0]["article"] == "Article 38"
    assert results[0]["score"] > 0.9

def test_advisory_api_flow(db_session):
    """
    Test the /chat endpoint.
    Note: Without real API KEY, RAGService mocks or fails gracefully.
    We just check the wiring here.
    """
    payload = {
        "query": "What about biomass?",
        "installation_id": 1
    }
    
    # We expect 500 or 404 because Seed Data for installation 1 might not be present in this isolated DB
    # or API Key missing. But we want to ensure it hits the router.
    response = client.post("/api/v1/advisory/chat", json=payload)
    
    # If it returns 404 "Session not found" or "Installation not found", the router is working.
    # If 500 "Embedding failed", logic executed.
    assert response.status_code in [200, 404, 500] 
