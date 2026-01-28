
from datetime import date, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.infrastructure.models import ComplianceTask, TaskStatus, Installation

class ProactiveMonitor:
    def __init__(self, db: Session):
        self.db = db

    async def check_deadline_compliance(self) -> List[Dict[str, Any]]:
        """
        Scan all pending tasks and identify those due within 7 days.
        """
        alerts = []
        upcoming_tasks = self.db.query(ComplianceTask).filter(
            ComplianceTask.status != TaskStatus.COMPLETED,
            ComplianceTask.due_date <= date.today() + timedelta(days=7)
        ).all()
        
        for task in upcoming_tasks:
            days_left = (task.due_date - date.today()).days
            alerts.append({
                "installation_id": task.installation_id,
                "installation_name": task.installation.name,
                "task_title": task.title_override or task.definition.title_en,
                "due_date": task.due_date,
                "days_remaining": days_left,
                "urgency": "CRITICAL" if days_left < 3 else "HIGH"
            })
            
        return alerts

    async def check_regulatory_changes(self) -> List[str]:
        """
        Mock of a service that would check EU OJ or APA website.
        """
        # In a real RAG app, this would query the vector DB for new documents inserted recently.
        return [
            "New guidance on Biomass sustainability (RED II) published.",
            "CBAM transition period reporting deadline approaching."
        ]

    async def benchmark_performance(self, installation_id: int) -> Dict[str, Any]:
        """Benchmark installation against sector averages (mocked)."""
        return {
            "specific_emissions": 0.18, # tCO2 / ton product
            "sector_average": 0.22,
            "performance": "Better than average",
            "tier_score": "High (Tier 2/3)"
        }
