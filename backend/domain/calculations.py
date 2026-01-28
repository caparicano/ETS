from typing import Dict, Any
from datetime import datetime
import math
from sqlalchemy.orm import Session
from asteval import Interpreter
from backend.infrastructure.models import SourceStream, EmissionFactor
from .schemas import TraceableCalculation

class GenericCalculationEngine:
    """Generic calculation engine driven by database configuration."""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize safe interpreter with standard math functions
        self.aeval = Interpreter(usersyms={"math": math, "round": round, "abs": abs})
    
    def calculate(
        self,
        source_stream_id: int,
        input_data: Dict[str, float],
        calculation_date: datetime
    ) -> TraceableCalculation:
        """
        Calculate emissions using configurable formula from source_stream.
        """
        # Get source stream configuration
        source_stream = self.db.query(SourceStream).filter_by(id=source_stream_id).first()
        if not source_stream:
            raise ValueError(f"Source stream {source_stream_id} not found")
        
        # Validate required inputs
        if not isinstance(source_stream.required_inputs, list):
             raise ValueError("Configuration Error: required_inputs must be a list")

        missing = set(source_stream.required_inputs) - set(input_data.keys())
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")
        
        # Fetch emission factors valid at calculation_date
        factors = self._get_factors(
            installation_id=source_stream.installation_id,
            fuel_type=source_stream.fuel_or_material,
            calculation_date=calculation_date
        )
        
        # Merge input_data with factors for formula evaluation
        context = {**input_data, **factors}
        
        # Parse and execute formula securely
        try:
            result = self._evaluate_formula(source_stream.formula_template, context)
        except Exception as e:
            raise ValueError(f"Formula evaluation failed: {e}")
        
        return TraceableCalculation(
            value=round(result, 4),
            unit="tCO2",
            formula=source_stream.formula_template,
            inputs_snapshot=input_data,
            factors_snapshot=factors,
            source_stream_name=source_stream.name,
            timestamp=datetime.now()
        )
    
    def _get_factors(
        self, 
        installation_id: int, 
        fuel_type: str, 
        calculation_date: datetime
    ) -> Dict[str, float]:
        """Fetch emission factors valid at given date."""
        factors_query = self.db.query(EmissionFactor).filter(
            EmissionFactor.installation_id == installation_id,
            EmissionFactor.fuel_type == fuel_type,
            EmissionFactor.valid_from <= calculation_date,
            (EmissionFactor.valid_to.is_(None)) | (EmissionFactor.valid_to >= calculation_date)
        )
        
        factors = {}
        for ef in factors_query.all():
            factors[ef.parameter_name] = ef.value
        
        return factors
    
    def _evaluate_formula(self, formula: str, context: Dict[str, Any]) -> float:
        """
        Safely evaluate formula using AST evaluation (no exec/eval).
        """
        # Inject context variables into the interpreter symbol table
        for key, value in context.items():
            self.aeval.symtable[key] = value
            
        # Execute
        result = self.aeval(formula)
        
        if len(self.aeval.error) > 0:
             error_msg = "; ".join([str(e) for e in self.aeval.error])
             raise ValueError(f"Calculation Error: {error_msg}")

        if result is None:
             raise ValueError("Formula returned No Value")
             
        return float(result)
