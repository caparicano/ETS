
import uuid
import json
from datetime import datetime, date
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.infrastructure.models import (
    WizardSession, WizardState, Installation, SourceStream, 
    EmissionFactor, ComplianceTask, TaskDefinition, InputFormDefinition,
    Organization, SectorType
)
from backend.domain.task_service import TaskGenerationService
from backend.domain.tegeh_parser import TEGEHParser

class WizardService:
    def __init__(self, db: Session):
        self.db = db
        self.parser = TEGEHParser()

    def create_session(self, organization_id: int) -> WizardSession:
        session_id = str(uuid.uuid4())
        session = WizardSession(
            id=session_id,
            organization_id=organization_id,
            state=WizardState.UPLOAD_PERMIT
        )
        self.db.add(session)
        self.db.commit()
        return session

    def handle_upload(self, session_id: str, file_bytes: bytes) -> Dict[str, Any]:
        session = self._get_session(session_id)
        
        # 1. Parse PDF
        parsed_data = self.parser.parse_pdf(file_bytes)
        
        # 2. Update Context
        context = session.context or {}
        context["parsed_permit"] = parsed_data
        session.context = context
        
        # 3. Advance State
        session.state = WizardState.CONFIRM_EQUIPMENT
        self.db.commit()
        
        # 4. Generate AI Message
        equip_list = ", ".join([e['name'] for e in parsed_data.get('equipment', [])])
        message = f"I analyzed the permit for **{parsed_data.get('installation_name')}**.\n\nI found the following emission sources:\n- {equip_list}\n\nIs this list correct?"
        
        return {
            "state": session.state,
            "message": message,
            "data": parsed_data
        }

    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        session = self._get_session(session_id)
        context = session.context
        
        response = {}
        
        if session.state == WizardState.CONFIRM_EQUIPMENT:
            # Assume user says "Yes" for MVP. 
            # Real version would refine list based on NLP.
            session.state = WizardState.FUEL_DETAILS
            
            # Formulate next question
            equip = context["parsed_permit"]["equipment"][0]
            response["message"] = f"Great. Now regarding **{equip['name']}**: What is the primary fuel source? (e.g. Natural Gas, Biomass)"
            
        elif session.state == WizardState.FUEL_DETAILS:
            # MVP: Assuming simple linear flow. Store input.
            if "fuel_details" not in context: context["fuel_details"] = {}
            
            # Simple heuristic: map last asked equip
            # In real app, we track which equipment we are discussing index-by-index
            equip_list = context["parsed_permit"]["equipment"]
            current_idx = len(context["fuel_details"])
            
            if current_idx < len(equip_list):
                current_equip = equip_list[current_idx]
                context["fuel_details"][current_equip["name"]] = user_message
                
                # Check if next equipment exists
                if current_idx + 1 < len(equip_list):
                    next_equip = equip_list[current_idx + 1]
                    response["message"] = f"Noted. And for **{next_equip['name']}**?"
                else:
                    # Done with fuels, move to Config Generation
                    session.state = WizardState.PREVIEW_CONFIG
                    config = self._generate_preview_config(context)
                    context["generated_config"] = config
                    response["message"] = "I have gathered all necessary information. I've prepared a Monitoring Plan and Compliance Schedule."
                    response["preview"] = config
            
        elif session.state == WizardState.PREVIEW_CONFIG:
            # Waiting for "Approve"
            pass

        session.context = context
        self.db.commit()
        return {
            "state": session.state,
            "message": response.get("message", "Processing..."),
            "preview": response.get("preview")
        }

    def approve_config(self, session_id: str) -> Installation:
        session = self._get_session(session_id)
        config = session.context.get("generated_config")
        
        if not config:
            raise ValueError("No configuration generated")
            
        # 1. Create Installation
        inst = Installation(
            name=config["installation_name"],
            permit_id=config["permit_id"],
            organization_id=session.organization_id
        )
        self.db.add(inst)
        self.db.commit()
        self.db.refresh(inst)
        
        # 2. Create Streams & Factors
        for stream_def in config["streams"]:
            stream = SourceStream(
                installation_id=inst.id,
                name=stream_def["name"],
                category="combustion",
                fuel_or_material=stream_def["fuel"],
                calculation_method="standard",
                tier=stream_def["tier"],
                formula_template=stream_def["formula"],
                required_inputs=stream_def["inputs"]
            )
            self.db.add(stream)
            self.db.commit()
            
            # Add Input Form
            form = InputFormDefinition(
                source_stream_id=stream.id,
                json_schema=stream_def["json_schema"]
            )
            self.db.add(form)

            # Factors
            for f in stream_def["factors"]:
                ef = EmissionFactor(
                    installation_id=inst.id,
                    fuel_type=stream_def["fuel"],
                    parameter_name=f["name"],
                    value=f["value"],
                    unit=f["unit"],
                    tier=1,
                    valid_from=datetime(2024,1,1),
                    source="MRR Default"
                )
                self.db.add(ef)

        # 3. Generate Tasks
        task_svc = TaskGenerationService(self.db)
        task_svc.generate_annual_tasks(inst.id, date.today().year)

        session.state = WizardState.COMPLETED
        self.db.commit()
        
        return inst

    def _get_session(self, session_id: str) -> WizardSession:
        return self.db.query(WizardSession).filter(WizardSession.id == session_id).first()

    def _generate_preview_config(self, context: Dict) -> Dict:
        """
        Translates interview context into DB-ready configuration structures.
        """
        permit = context["parsed_permit"]
        fuels = context["fuel_details"]
        
        streams = []
        for equip_name, fuel_raw in fuels.items():
            fuel_key = "natural_gas" if "gas" in fuel_raw.lower() else "biomass"
            
            # Logic for NG
            if fuel_key == "natural_gas":
                streams.append({
                    "name": f"{equip_name} (Combustion)",
                    "fuel": "natural_gas",
                    "tier": 2, # MRR Default
                    "formula": "activity_data * ncv * ef * of * 0.001",
                    "inputs": ["activity_data"],
                    "json_schema": {
                        "type": "object",
                        "title": f"Gas Consumption - {equip_name}",
                        "properties": {
                            "activity_data": {"type": "number", "title": "Meter Reading (Nm3)", "unit": "Nm3"}
                        },
                        "required": ["activity_data"]
                    },
                    "factors": [
                        {"name": "ncv", "value": 0.03854, "unit": "GJ/Nm3"},
                        {"name": "ef", "value": 56.1, "unit": "kgCO2/GJ"},
                        {"name": "of", "value": 1.0, "unit": "fraction"}
                    ]
                })
        
        return {
            "installation_name": permit.get("installation_name", "New Installation"),
            "permit_id": permit.get("permit_id", "PENDING"),
            "streams": streams
        }
