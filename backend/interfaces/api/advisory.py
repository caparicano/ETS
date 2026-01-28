
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.infrastructure.database import get_db
from backend.infrastructure.auth import get_current_user
from backend.infrastructure.models import User
from backend.domain.rag_service import RAGService
from backend.domain.strategic_analysis import StrategicAnalyzer

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    installation_id: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    session_id: str

@router.post("/api/v1/advisory/chat", response_model=ChatResponse)
async def chat_with_consultant(
    request: ChatRequest = Body(...),
    session_id: Optional[str] = None, # If none, creates new
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Strategic Advisory Endpoint.
    """
    rag = RAGService(db)
    
    # Init session if needed
    if not session_id:
        context = {}
        if request.installation_id:
            context['installation_id'] = request.installation_id
        session_id = rag.create_session(current_user.id, context)
    
    # Get Advice
    try:
        result = rag.ask(session_id, request.query)
        return ChatResponse(
            answer=result['answer'],
            citations=result['citations'],
            session_id=session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/advisory/analyze-impact")
async def analyze_regulatory_impact(
    installation_id: int = Body(..., embed=True),
    topic: str = Body(..., embed=True), # e.g. "CBAM", "Free Allocation 2026"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Specialized endpoint for generating impact reports.
    """
    rag = RAGService(db)
    session_id = rag.create_session(current_user.id, {'installation_id': installation_id})
    
    prompt = f"Analyze the impact of '{topic}' on my installation considering my current source streams and sector. Highlight financial risks."
    
    result = rag.ask(session_id, prompt)
    
    return {
        "analysis": result['answer'],
        "key_regulations": result['citations']
    }

@router.post("/api/v1/advisory/analyze-fuel-switch")
async def analyze_fuel_switch(
    installation_id: int = Body(...),
    from_fuel: str = Body(...),
    to_fuel: str = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """ROI Calculator for Fuel Switching."""
    analyzer = StrategicAnalyzer(db)
    try:
        return analyzer.analyze_fuel_switch(installation_id, from_fuel, to_fuel)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/api/v1/advisory/detect-anomalies")
async def detect_anomalies(
    installation_id: int = Body(...),
    year: int = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Statistical anomaly detection."""
    analyzer = StrategicAnalyzer(db)
    return analyzer.detect_anomalies(installation_id, year)
