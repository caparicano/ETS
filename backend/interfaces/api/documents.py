
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import hashlib
import os

from backend.infrastructure.database import get_db
from backend.infrastructure.models import Document, AuditLog, User, DocStatus, DocumentValidationRule
from backend.infrastructure.storage import LocalStorageService
from backend.infrastructure.auth import get_current_user
from backend.domain.ocr_service import OCRService
from backend.domain.schemas import DocumentResponse

router = APIRouter()
storage_service = LocalStorageService()
ocr_service = OCRService()

def calculate_file_hash(file: UploadFile) -> str:
    """Calculates SHA-256 hash of file content"""
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file.file.read(4096), b""):
        sha256_hash.update(byte_block)
    file.file.seek(0)
    return sha256_hash.hexdigest()

@router.get("/api/v1/documents", response_model=List[DocumentResponse])
async def list_documents(
    installation_id: int,
    year: Optional[int] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List documents for an installation."""
    query = db.query(Document).filter(Document.installation_id == installation_id)
    
    # Simple tenancy check logic (assuming installation access is checked elsewhere or we check org match here)
    # In production, join with Installation and check organization_id
    
    if year:
        query = query.filter(Document.reporting_year == year)
    if type:
        query = query.filter(Document.document_type == type)
        
    docs = query.order_by(desc(Document.upload_date)).all()
    
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            document_type=d.document_type,
            reporting_year=d.reporting_year or 0,
            status=d.status,
            version=d.version,
            upload_date=d.upload_date,
            extracted_text_snippet=d.extracted_text[:200] if d.extracted_text else None,
            file_path=d.file_path,
            locked_at=d.locked_at
        ) for d in docs
    ]

@router.post("/api/v1/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    installation_id: int = Form(...),
    reporting_year: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Secure upload for APA Evidence with OCR Verification.
    Checks file rules against DocumentValidationRule table.
    """
    
    # 1. Fetch Validation Rule from DB
    rule = db.query(DocumentValidationRule).filter(
        DocumentValidationRule.document_type == document_type,
        (DocumentValidationRule.organization_id == current_user.organization_id) | (DocumentValidationRule.organization_id.is_(None))
    ).order_by(DocumentValidationRule.organization_id.nulls_last()).first()

    if not rule:
        allowed = [".pdf"]
        must_contain = []
    else:
        allowed = rule.allowed_formats
        must_contain = rule.must_contain_keywords or []

    # Check Extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Formato inválido. Aceites: {', '.join(allowed)}"
        )
    
    # Read file content for Hashing & OCR
    content_bytes = await file.read()
    
    # 2. OCR & Content Validation
    extracted_text = None
    validation_status = DocStatus.PENDING
    
    if must_contain and file_ext in ['.pdf', '.jpg', '.png']:
        mime_type = file.content_type or "application/pdf"
        extracted_text = ocr_service.extract_text(content_bytes, mime_type)
        
        if not ocr_service.validate_content(extracted_text, must_contain):
             validation_status = DocStatus.OCR_FAILED
    
    # Reset cursor
    file.file.seek(0) 

    # 3. Calculate Hash (using the bytes we already read)
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()
    
    # 4. Versioning Logic
    last_version = db.query(Document).filter(
        Document.installation_id == installation_id,
        Document.document_type == document_type,
        Document.reporting_year == reporting_year
    ).order_by(desc(Document.version)).first()
    
    new_version = (last_version.version + 1) if last_version else 1
    
    # 5. Save Physical File
    safe_filename = f"{document_type}_v{new_version}{file_ext}"
    storage_path = f"{installation_id}/{reporting_year}/{safe_filename}"
    
    # Re-wrap bytes for storage
    import io
    saved_path = storage_service.save(io.BytesIO(content_bytes), storage_path)
    
    # 6. Create DB Record
    new_doc = Document(
        filename=file.filename,
        file_path=saved_path,
        file_hash=sha256_hash,
        document_type=document_type,
        reporting_year=reporting_year,
        version=new_version,
        uploaded_by_id=current_user.id,
        installation_id=installation_id,
        status=validation_status,
        extracted_text=extracted_text
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # 7. Audit Log
    audit = AuditLog(
        entity_type="Document",
        entity_id=new_doc.id,
        action="UPLOAD",
        changes={
            "filename": file.filename, 
            "version": new_version, 
            "ocr_status": validation_status,
            "keywords_checked": must_contain
        },
        user_id=current_user.id
    )
    db.add(audit)
    db.commit()
    
    response_msg = "Documento carregado com sucesso."
    if validation_status == DocStatus.OCR_FAILED:
        response_msg = f"Aviso: O documento não contém as palavras-chave obrigatórias: {', '.join(must_contain)}"
    
    return {
        "id": new_doc.id,
        "filename": new_doc.filename,
        "version": new_version,
        "status": validation_status,
        "message": response_msg,
        "extracted_text_snippet": extracted_text[:100] if extracted_text else None
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
