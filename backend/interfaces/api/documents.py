from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import hashlib
import os

from backend.infrastructure.database import get_db
from backend.infrastructure.models import Document, AuditLog, User, DocStatus, DocumentValidationRule
from backend.infrastructure.storage import LocalStorageService
from backend.infrastructure.auth import get_current_user # Updated to use real auth

router = APIRouter()
storage_service = LocalStorageService()

def calculate_file_hash(file: UploadFile) -> str:
    """Calculates SHA-256 hash of file content"""
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.file.seek(0)
    return sha256_hash.hexdigest()

@router.post("/api/v1/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...), # Now string, validated against DB
    installation_id: int = Form(...),
    reporting_year: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Secure upload for APA Evidence.
    Checks file rules against DocumentValidationRule table.
    """
    
    # 1. Fetch Validation Rule from DB
    # Check for specific organization rule, fallback to global (org_id is null)
    rule = db.query(DocumentValidationRule).filter(
        DocumentValidationRule.document_type == document_type,
        (DocumentValidationRule.organization_id == current_user.organization_id) | (DocumentValidationRule.organization_id.is_(None))
    ).order_by(DocumentValidationRule.organization_id.nulls_last()).first()

    if not rule:
        # Fallback default if no rule exists (for MVP robustness)
        allowed = [".pdf"]
    else:
        allowed = rule.allowed_formats

    # Check Extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido. Aceites: {', '.join(allowed)}"
        )

    # 2. Calculate Hash
    file_hash = calculate_file_hash(file)
    
    # 3. Versioning Logic
    last_version = db.query(Document).filter(
        Document.installation_id == installation_id,
        Document.document_type == document_type,
        Document.reporting_year == reporting_year
    ).order_by(desc(Document.version)).first()
    
    new_version = (last_version.version + 1) if last_version else 1
    
    # 4. Save Physical File
    safe_filename = f"{document_type}_v{new_version}{file_ext}"
    storage_path = f"{installation_id}/{reporting_year}/{safe_filename}"
    
    saved_path = storage_service.save(file.file, storage_path)
    
    # 5. Create DB Record
    new_doc = Document(
        filename=file.filename,
        file_path=saved_path,
        file_hash=file_hash,
        document_type=document_type,
        reporting_year=reporting_year,
        version=new_version,
        uploaded_by_id=current_user.id,
        installation_id=installation_id,
        status=DocStatus.PENDING
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # 6. Audit Log
    audit = AuditLog(
        entity_type="Document",
        entity_id=new_doc.id,
        action="UPLOAD",
        changes={"filename": file.filename, "version": new_version},
        user_id=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return {
        "id": new_doc.id,
        "filename": new_doc.filename,
        "version": new_version,
        "status": "uploaded",
        "message": "Documento carregado com sucesso."
    }

@router.post("/api/v1/documents/{document_id}/lock")
async def lock_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lock a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
        
    if doc.locked_at:
         raise HTTPException(status_code=400, detail="Documento já se encontra bloqueado")
         
    doc.status = DocStatus.LOCKED
    doc.locked_at = func.now()
    
    audit = AuditLog(
        entity_type="Document",
        entity_id=doc.id,
        action="LOCK",
        user_id=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return {"status": "locked", "locked_at": doc.locked_at}
