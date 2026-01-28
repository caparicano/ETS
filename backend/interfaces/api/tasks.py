
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import List, Optional
from datetime import date, datetime

from backend.infrastructure.database import get_db
from backend.infrastructure.auth import get_current_user
from backend.infrastructure.models import User, ComplianceTask, AuditLog, TaskStatus, Installation
from backend.domain.schemas import TaskResponse, NextDeadlineResponse
from backend.domain.task_service import TaskGenerationService

router = APIRouter()

@router.get("/api/v1/tasks", response_model=List[TaskResponse])
async def get_tasks(
    installation_id: int,
    status_filter: Optional[str] = None, # pending, overdue, completed
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List compliance tasks for an installation."""
    # 1. Tenancy Check
    installation = db.query(Installation).filter(Installation.id == installation_id).first()
    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")
    if installation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Lazy Generation (Ensure tasks exist for current year)
    # In prod, this would be a cron job. For MVP, we check on read.
    current_year = year if year else date.today().year
    # We trigger generation for the previous year too (reporting year is usually Y-1)
    reporting_year = current_year if year else current_year - 1
    
    svc = TaskGenerationService(db)
    svc.generate_annual_tasks(installation_id, reporting_year)
    
    # 3. Query
    query = db.query(ComplianceTask).join(ComplianceTask.definition).filter(
        ComplianceTask.installation_id == installation_id
    )
    
    if year:
        query = query.filter(ComplianceTask.reporting_year == year)
        
    if status_filter:
        if status_filter.upper() in TaskStatus.__members__:
             query = query.filter(ComplianceTask.status == TaskStatus[status_filter.upper()])
             
    # Sort by due date
    tasks = query.order_by(asc(ComplianceTask.due_date)).all()
    
    return [
        TaskResponse(
            id=t.id,
            title=t.title_override or t.definition.title_pt,
            task_code=t.definition.task_code,
            description=t.definition.description_pt,
            due_date=t.due_date,
            status=t.status,
            priority=t.definition.priority,
            reporting_year=t.reporting_year,
            period_month=t.period_month,
            category=t.definition.task_code # simple cat map for now
        ) for t in tasks
    ]

@router.post("/api/v1/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a task as completed."""
    task = db.query(ComplianceTask).filter(ComplianceTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.installation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if task.status == TaskStatus.COMPLETED:
        return _map_to_response(task)

    # Update
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    task.completed_by_user_id = current_user.id
    
    # Audit
    audit = AuditLog(
        entity_type="ComplianceTask",
        entity_id=task.id,
        action="COMPLETE_TASK",
        changes={"status": "COMPLETED"},
        user_id=current_user.id
    )
    db.add(audit)
    db.commit()
    
    return _map_to_response(task)

@router.get("/api/v1/tasks/next-deadline", response_model=NextDeadlineResponse)
async def get_next_deadline(
    installation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the single most urgent pending task."""
    # Tenancy check omitted for brevity (covered in get_tasks logic mostly, but good to add)
    installation = db.query(Installation).filter(Installation.id == installation_id).first()
    if not installation or installation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate first to be sure
    reporting_year = date.today().year - 1
    svc = TaskGenerationService(db)
    svc.generate_annual_tasks(installation_id, reporting_year)

    task = db.query(ComplianceTask).filter(
        ComplianceTask.installation_id == installation_id,
        ComplianceTask.status != TaskStatus.COMPLETED,
        ComplianceTask.due_date >= date.today()
    ).order_by(asc(ComplianceTask.due_date)).first()
    
    if not task:
        return NextDeadlineResponse()
        
    days = (task.due_date - date.today()).days
    
    return NextDeadlineResponse(
        task=_map_to_response(task),
        days_remaining=days
    )

def _map_to_response(t: ComplianceTask) -> TaskResponse:
    return TaskResponse(
        id=t.id,
        title=t.title_override or t.definition.title_pt,
        task_code=t.definition.task_code,
        description=t.definition.description_pt,
        due_date=t.due_date,
        status=t.status,
        priority=t.definition.priority,
        reporting_year=t.reporting_year,
        period_month=t.period_month
    )
