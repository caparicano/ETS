
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os

from backend.main import app
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.models import (
    Installation, Organization, SectorType, TaskDefinition, 
    ComplianceTask, RecurrenceType, WeekendRule, User
)
from backend.domain.task_service import TaskGenerationService
from backend.infrastructure.seed_data import seed_initial_data

# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tasks.db"
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
    seed_initial_data(db) # This seeds Org 1, Inst 1, and APA Tasks
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_tasks.db"):
        os.remove("./test_tasks.db")

def test_annual_task_generation(db_session):
    """Test that standard annual tasks (RE, Verification) are generated."""
    svc = TaskGenerationService(db_session)
    
    # Generate for 2023 (Due 2024)
    tasks = svc.generate_annual_tasks(1, 2023)
    
    assert len(tasks) > 0
    
    # Check RE Task
    re_task = next((t for t in tasks if t.definition.task_code == "submit_re"), None)
    assert re_task is not None
    assert re_task.reporting_year == 2023
    
    # Due Date Check (fixed 31 March of next year = 2024-03-31)
    # 2024-03-31 is a Sunday. 
    # Weekend Rule is SHIFT_FORWARD -> Should be 2024-04-01
    assert re_task.due_date == date(2024, 4, 1)

def test_monthly_task_generation(db_session):
    """Test that monthly input tasks are generated x12."""
    svc = TaskGenerationService(db_session)
    
    # Already generated in previous test, but check count
    all_tasks = db_session.query(ComplianceTask).filter_by(
        installation_id=1, 
        reporting_year=2023
    ).all()
    
    monthly_tasks = [t for t in all_tasks if t.definition.recurrence_type == RecurrenceType.MONTHLY]
    
    # Should be 12 tasks
    assert len(monthly_tasks) == 12
    
    # Check January Task
    jan_task = next(t for t in monthly_tasks if t.period_month == 1)
    # Jan 2023 data -> Due Feb 15, 2023 (Year=Reporting Year for Monthly)
    # Wait, in logic: due_year = year (2023) if month < 12.
    # Feb 15 2023 is Wednesday. No shift.
    assert jan_task.due_date == date(2023, 2, 15)

def test_api_get_tasks(db_session):
    """Test API endpoint lists tasks."""
    response = client.get("/api/v1/tasks?installation_id=1&year=2023")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["status"] == "PENDING"

def test_api_next_deadline(db_session):
    """Test dashboard 'next deadline' logic."""
    # Ensure there is a future task
    # If we ran generation for 2023, due dates are in 2023/2024.
    # Current date in test is real time (e.g. 2025). So 2024 tasks are OVERDUE/past.
    # Let's generate for current year - 1
    current_year = date.today().year
    reporting_year = current_year - 1 
    
    svc = TaskGenerationService(db_session)
    svc.generate_annual_tasks(1, reporting_year)
    
    response = client.get("/api/v1/tasks/next-deadline?installation_id=1")
    assert response.status_code == 200
    data = response.json()
    
    # We should get a task
    if data.get("task"):
        assert "days_remaining" in data
