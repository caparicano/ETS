
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.infrastructure.models import (
    Installation, TaskDefinition, ComplianceTask, TaskStatus, 
    RecurrenceType, WeekendRule, SectorType
)
import calendar

class TaskGenerationService:
    def __init__(self, db: Session):
        self.db = db

    def generate_annual_tasks(self, installation_id: int, year: int) -> List[ComplianceTask]:
        """
        Generate compliance tasks for a specific installation and year.
        Idempotent: Checks if tasks already exist to avoid duplicates.
        """
        installation = self.db.query(Installation).get(installation_id)
        if not installation:
            raise ValueError("Installation not found")
        
        # 1. Fetch applicable definitions
        definitions = self._get_applicable_definitions(installation)
        
        generated_tasks = []
        
        for defn in definitions:
            if defn.recurrence_type == RecurrenceType.ANNUAL:
                task = self._create_task_instance(installation_id, defn, year)
                if task: generated_tasks.append(task)
            
            elif defn.recurrence_type == RecurrenceType.MONTHLY:
                for month in range(1, 13):
                    task = self._create_task_instance(installation_id, defn, year, month)
                    if task: generated_tasks.append(task)
                    
        self.db.commit()
        return generated_tasks

    def _get_applicable_definitions(self, installation: Installation) -> List[TaskDefinition]:
        """Filter definitions by sector."""
        query = self.db.query(TaskDefinition)
        
        # Filter by sector if defined, or allow generic (NULL)
        if installation.organization.sector:
            query = query.filter(
                (TaskDefinition.sector_filter == installation.organization.sector) |
                (TaskDefinition.sector_filter.is_(None))
            )
        
        return query.all()

    def _create_task_instance(
        self, 
        installation_id: int, 
        defn: TaskDefinition, 
        year: int, 
        month: Optional[int] = None
    ) -> Optional[ComplianceTask]:
        """Creates a single task instance if it doesn't exist."""
        
        # Check existence
        query = self.db.query(ComplianceTask).filter(
            ComplianceTask.installation_id == installation_id,
            ComplianceTask.definition_id == defn.id,
            ComplianceTask.reporting_year == year
        )
        
        if month:
            query = query.filter(ComplianceTask.period_month == month)
            
        if query.first():
            return None # Already exists
            
        # Calculate Due Date
        due_date = self._calculate_deadline(defn, year, month)
        due_date = self._apply_weekend_rule(due_date, defn.weekend_rule)
        
        # Construct Title
        title = defn.title_pt
        if month:
            month_name = calendar.month_name[month]
            title = f"{title} ({month_name})"
            
        task = ComplianceTask(
            installation_id=installation_id,
            definition_id=defn.id,
            reporting_year=year,
            period_month=month,
            due_date=due_date,
            status=TaskStatus.PENDING,
            title_override=title
        )
        
        self.db.add(task)
        return task

    def _calculate_deadline(self, defn: TaskDefinition, year: int, month: Optional[int]) -> date:
        """
        Calculates the raw deadline before weekend adjustment.
        """
        target_year = year # Typically deadlines are in the same year or next year (handled by definition logic)
        
        if defn.deadline_type == "fixed_date":
            # Simple fixed date (e.g., 31 March of NEXT year for Annual reports)
            # Assumption: Annual tasks for '2024' are due in '2025' usually.
            # For simplicity in this logic, we assume the definition deadline_month/year 
            # implies the due date year. 
            # Ideally, we map: Reporting Year 2024 -> Due 2025.
            # Let's assume input 'year' is the REPORTING year.
            
            due_year = year + 1 # Most compliance tasks are due the following year
            
            # Special case: If deadline is late in the year (e.g. Nov/Dec), maybe it's same year?
            # For standard EU ETS: RE (Mar), Verification (Mar), Surrender (Apr) are all Y+1.
            
            if defn.recurrence_type == RecurrenceType.MONTHLY:
                # Monthly tasks are usually due next month
                if not month: raise ValueError("Month required for monthly task")
                
                # Logic: Jan 2024 data -> Due Feb 2024
                if month == 12:
                    due_year = year + 1
                    due_month = 1
                else:
                    due_year = year
                    due_month = month + 1
                
                # Use fixed day if provided (e.g. 15th), or relative offset
                day = defn.deadline_day if defn.deadline_day else 15
                try:
                    return date(due_year, due_month, day)
                except ValueError:
                    # Handle Feb 30 etc -> limit to last day of month
                    last_day = calendar.monthrange(due_year, due_month)[1]
                    return date(due_year, due_month, last_day)

            else:
                # Annual Tasks
                return date(due_year, defn.deadline_month, defn.deadline_day)

        elif defn.deadline_type == "relative":
            # Relative to period end
            # Annual Period End: Dec 31, YYYY
            # Monthly Period End: Last day of Month, YYYY
            
            if defn.recurrence_type == RecurrenceType.ANNUAL:
                base_date = date(year, 12, 31)
            else:
                last_day = calendar.monthrange(year, month)[1]
                base_date = date(year, month, last_day)
                
            return base_date + timedelta(days=defn.deadline_offset_days)
            
        return date(year, 12, 31) # Fallback

    def _apply_weekend_rule(self, d: date, rule: WeekendRule) -> date:
        if rule == WeekendRule.ALLOW:
            return d
            
        weekday = d.weekday() # 0=Mon, 5=Sat, 6=Sun
        
        if weekday == 5: # Saturday
            if rule == WeekendRule.SHIFT_FORWARD:
                return d + timedelta(days=2) # Mon
            elif rule == WeekendRule.SHIFT_BACKWARD:
                return d - timedelta(days=1) # Fri
        elif weekday == 6: # Sunday
            if rule == WeekendRule.SHIFT_FORWARD:
                return d + timedelta(days=1) # Mon
            elif rule == WeekendRule.SHIFT_BACKWARD:
                return d - timedelta(days=2) # Fri
                
        return d
