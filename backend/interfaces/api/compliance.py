
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from backend.infrastructure.database import get_db
from backend.infrastructure.auth import get_current_user
from backend.infrastructure.models import User, InputFormDefinition, SourceStream, EmissionEntry, AuditLog
from backend.domain.schemas import InputFormDefinitionResponse, EmissionEntryCreate, EmissionEntryResponse
from backend.domain.calculations import GenericCalculationEngine

router = APIRouter()

@router.get("/api/v1/source-streams/{stream_id}/form-definition", response_model=InputFormDefinitionResponse)
async def get_form_definition(
    stream_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the JSON Schema to render the input form for a specific source stream.
    Enforces that the stream belongs to the user's organization.
    """
    stream = db.query(SourceStream).filter(SourceStream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Source stream not found")
        
    # Tenancy check
    if stream.installation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied to this installation")
        
    form_def = db.query(InputFormDefinition).filter(InputFormDefinition.source_stream_id == stream_id).first()
    if not form_def:
        raise HTTPException(status_code=404, detail="Form definition not found for this stream")
        
    return InputFormDefinitionResponse(
        source_stream_id=stream.id,
        source_stream_name=stream.name,
        json_schema=form_def.json_schema,
        ui_schema=form_def.ui_schema
    )

@router.post("/api/v1/emission-entries", response_model=EmissionEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_emission_entry(
    entry_data: EmissionEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit data -> Calculate Emissions (Traceable) -> Persist -> Audit Log.
    """
    # 1. Fetch Stream & Validate Access
    stream = db.query(SourceStream).filter(SourceStream.id == entry_data.source_stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Source stream not found")
        
    if stream.installation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    # 2. Run Calculation Engine
    engine = GenericCalculationEngine(db)
    
    # We use the period_start for finding valid emission factors
    calc_date = datetime.combine(entry_data.period_start, datetime.min.time())
    
    try:
        result = engine.calculate(
            source_stream_id=stream.id,
            input_data=entry_data.input_data,
            calculation_date=calc_date
        )
        # Add regulatory basis from the logic context (engine should ideally provide this, for now we inject generic)
        result.regulatory_basis = "MRR 2018/2066 Annex IV (Standard Method)"
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # 3. Create Entry Record
    new_entry = EmissionEntry(
        installation_id=stream.installation_id,
        source_stream_id=stream.id,
        date_start=entry_data.period_start,
        date_end=entry_data.period_end,
        source_stream_name=stream.name, # Snapshot
        calculated_tco2=result.value,
        calculation_trace=result.dict(),
        is_verified=False
    )
    
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    # 4. Audit Log
    audit = AuditLog(
        entity_type="EmissionEntry",
        entity_id=new_entry.id,
        action="CREATE_CALCULATION",
        changes={"input": entry_data.input_data, "result": result.value},
        user_id=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return EmissionEntryResponse(
        id=new_entry.id,
        source_stream_name=new_entry.source_stream_name,
        calculated_tco2=new_entry.calculated_tco2,
        date_start=new_entry.date_start,
        date_end=new_entry.date_end,
        calculation_trace=result
    )
