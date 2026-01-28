
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from backend.infrastructure.models import TaskStatus

class TraceableCalculation(BaseModel):
    """The output of any compliance calculation. Must include the 'Why'."""
    value: float
    unit: str
    formula: str 
    source_stream_name: str
    inputs_snapshot: Dict[str, Any]
    factors_snapshot: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    regulatory_basis: Optional[str] = None

class GenericCalculationInput(BaseModel):
    source_stream_id: int
    data: Dict[str, float]
    calculation_date: Optional[datetime] = None

# --- Phase 1.1 Form Schemas ---

class InputFormDefinitionResponse(BaseModel):
    source_stream_id: int
    source_stream_name: str
    json_schema: Dict[str, Any]
    ui_schema: Optional[Dict[str, Any]] = {}

class EmissionEntryCreate(BaseModel):
    source_stream_id: int
    period_start: date
    period_end: date
    input_data: Dict[str, float] # Matches the schema definition

class EmissionEntryResponse(BaseModel):
    id: int
    source_stream_name: str
    calculated_tco2: float
    date_start: datetime
    date_end: datetime
    calculation_trace: TraceableCalculation

# --- Phase 1.2 Task Schemas ---

class TaskResponse(BaseModel):
    id: int
    title: str
    task_code: str
    description: Optional[str]
    due_date: date
    status: TaskStatus
    priority: int
    reporting_year: int
    period_month: Optional[int] = None
    category: str = "Compliance"

class NextDeadlineResponse(BaseModel):
    task: Optional[TaskResponse] = None
    days_remaining: Optional[int] = None
