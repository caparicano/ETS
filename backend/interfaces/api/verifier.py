
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from typing import Optional
from pydantic import BaseModel

from backend.infrastructure.database import get_db
from backend.infrastructure.auth import get_current_user
from backend.infrastructure.models import User, VerifierAccess, Installation, EmissionEntry
from backend.domain.report_generator import APAReportGenerator

router = APIRouter()

class GrantAccessRequest(BaseModel):
    installation_id: int
    verifier_email: str
    expires_days: int = 30

class VerifierAccessLink(BaseModel):
    access_token: str
    expires_at: datetime
    dashboard_url: str

class VerifierDashboardData(BaseModel):
    installation_name: str
    permit_id: str
    total_emissions_ytd: float
    entries_count: int

@router.post("/api/v1/verifier/grant-access", response_model=VerifierAccessLink)
async def grant_verifier_access(
    request: GrantAccessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate time-limited access link for external verifier."""
    inst = db.query(Installation).get(request.installation_id)
    if not inst: raise HTTPException(404, "Installation not found")
    if inst.organization_id != current_user.organization_id:
        raise HTTPException(403, "Access denied")
        
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=request.expires_days)
    
    access = VerifierAccess(
        token=token,
        installation_id=request.installation_id,
        verifier_email=request.verifier_email,
        created_by_user_id=current_user.id,
        expires_at=expires
    )
    db.add(access)
    db.commit()
    
    return VerifierAccessLink(
        access_token=token,
        expires_at=expires,
        dashboard_url=f"/verifier/dashboard/{token}"
    )

@router.get("/api/v1/verifier/dashboard/{token}", response_model=VerifierDashboardData)
async def verifier_dashboard(token: str, db: Session = Depends(get_db)):
    """Read-only view for verifiers."""
    access = db.query(VerifierAccess).filter(
        VerifierAccess.token == token,
        VerifierAccess.is_revoked == False,
        VerifierAccess.expires_at > datetime.now()
    ).first()
    
    if not access:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
        
    inst = access.installation
    
    # Simple aggregations
    entries_count = db.query(EmissionEntry).filter(EmissionEntry.installation_id == inst.id).count()
    total_emissions = 0.0 # Calculate YTD logic here if needed
    
    return VerifierDashboardData(
        installation_name=inst.name,
        permit_id=inst.permit_id,
        total_emissions_ytd=total_emissions,
        entries_count=entries_count
    )

@router.get("/api/v1/verifier/download-report/{token}")
async def download_report_for_verifier(token: str, year: int, db: Session = Depends(get_db)):
    """Allow verifier to download official PDF."""
    access = db.query(VerifierAccess).filter(
        VerifierAccess.token == token,
        VerifierAccess.expires_at > datetime.now()
    ).first()
    if not access: raise HTTPException(403, "Invalid token")
    
    gen = APAReportGenerator(db)
    pdf_bytes = gen.generate_relatorio_emissoes(access.installation_id, year)
    
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf")
