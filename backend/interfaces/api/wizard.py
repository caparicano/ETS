
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.infrastructure.database import get_db
from backend.infrastructure.auth import get_current_user
from backend.infrastructure.models import User
from backend.domain.wizard_service import WizardService

router = APIRouter()

class InterviewMessage(BaseModel):
    message: str

class WizardResponse(BaseModel):
    session_id: str
    state: str
    message: str
    data: Optional[Dict[str, Any]] = None
    preview: Optional[Dict[str, Any]] = None

@router.post("/api/v1/wizard/start")
async def start_wizard(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 1: Create session and parse PDF.
    """
    svc = WizardService(db)
    session = svc.create_session(current_user.organization_id)
    
    file_bytes = await file.read()
    result = svc.handle_upload(session.id, file_bytes)
    
    return WizardResponse(
        session_id=session.id,
        state=result["state"],
        message=result["message"],
        data=result["data"]
    )

@router.post("/api/v1/wizard/{session_id}/message")
async def interview_chat(
    session_id: str,
    body: InterviewMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 2: Conversational Loop.
    """
    svc = WizardService(db)
    result = svc.process_message(session_id, body.message)
    
    return WizardResponse(
        session_id=session_id,
        state=result["state"],
        message=result["message"],
        preview=result.get("preview")
    )

@router.post("/api/v1/wizard/{session_id}/approve")
async def approve_config(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 3: Commit Config.
    """
    svc = WizardService(db)
    try:
        inst = svc.approve_config(session_id)
        return {"status": "success", "installation_id": inst.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
