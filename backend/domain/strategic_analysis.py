
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from backend.infrastructure.models import Installation, SourceStream, EmissionEntry, EmissionFactor

class StrategicAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def analyze_fuel_switch(self, installation_id: int, from_fuel: str, to_fuel: str) -> Dict[str, Any]:
        """
        Calculate ROI for fuel switching (e.g., natural gas -> biomass).
        Returns CAPEX, OPEX savings, Payback, and Regulatory context.
        """
        # 1. Fetch Installation & Current Consumption
        inst = self.db.query(Installation).get(installation_id)
        if not inst: raise ValueError("Installation not found")
        
        # Estimate annual consumption (sum of last 12 months for 'from_fuel')
        # Simplified: Get all entries for streams using 'from_fuel'
        streams = [s for s in inst.source_streams if s.fuel_or_material == from_fuel]
        total_emissions = 0.0
        total_energy_gj = 0.0
        
        for s in streams:
            entries = self.db.query(EmissionEntry).filter(
                EmissionEntry.source_stream_id == s.id
            ).all()
            for e in entries:
                total_emissions += e.calculated_tco2
                # Reverse engineer Energy: Emissions / EF (approx)
                # Ideally we store Activity Data directly. For MVP we assume activity_data stored in trace
                if 'activity_data_nm3' in e.calculation_trace.get('inputs_snapshot', {}):
                    vol = e.calculation_trace['inputs_snapshot']['activity_data_nm3']
                    ncv = e.calculation_trace['factors_snapshot'].get('ncv', 0.038)
                    total_energy_gj += vol * ncv

        # 2. Market Assumptions (Mocked or Configured)
        eua_price = 85.0 # Euro/tCO2
        fuel_prices = {
            "natural_gas": 15.0, # Euro/GJ
            "biomass": 12.0 # Euro/GJ
        }
        
        current_fuel_cost = total_energy_gj * fuel_prices.get(from_fuel, 0)
        current_carbon_cost = total_emissions * eua_price
        
        # 3. Target Scenario
        # Biomass EF = 0 (Sustainable)
        new_carbon_cost = 0.0 if to_fuel == "biomass" else (total_energy_gj * 56.1 * 0.001 * eua_price) # Fallback logic
        new_fuel_cost = total_energy_gj * fuel_prices.get(to_fuel, 0)
        
        annual_opex_savings = (current_fuel_cost + current_carbon_cost) - (new_fuel_cost + new_carbon_cost)
        
        # CAPEX Estimation (Heuristic based on capacity)
        # Assume 100k EUR per MW, approx 1 MW = 3600 MJ/h. Very rough estimate.
        capex_estimate = 500000.0 # Placeholder
        
        payback_years = capex_estimate / annual_opex_savings if annual_opex_savings > 0 else 999
        
        return {
            "current_annual_cost": round(current_fuel_cost + current_carbon_cost, 2),
            "projected_annual_cost": round(new_fuel_cost + new_carbon_cost, 2),
            "annual_savings": round(annual_opex_savings, 2),
            "capex_estimate": capex_estimate,
            "payback_period_years": round(payback_years, 1),
            "regulatory_requirements": [
                "RED II Sustainability Certification required for zero-rating (MRR Article 38)",
                "Update Monitoring Plan significantly (Article 12)"
            ],
            "citation": "[MRR Article 38, Annex IV]"
        }

    def analyze_tier_upgrade(self, source_stream_id: int, target_tier: int) -> Dict[str, Any]:
        """Assess feasibility of Tier upgrade."""
        stream = self.db.query(SourceStream).get(source_stream_id)
        if not stream: raise ValueError("Stream not found")
        
        current_tier = stream.tier
        
        return {
            "current_tier": current_tier,
            "target_tier": target_tier,
            "feasibility": "High" if target_tier <= current_tier + 1 else "Medium",
            "technical_requirements": [
                f"Meter uncertainty must be < {1.5 if target_tier == 4 else 2.5}% (MRR Article 28)",
                "Calibration by accredited lab required every 2 years"
            ],
            "benefit": "Reduced uncertainty factor in uncertainty assessment, lower risk of over-reporting.",
            "citation": "[MRR Article 26-29]"
        }

    def detect_anomalies(self, installation_id: int, period_year: int) -> List[Dict[str, Any]]:
        """Identify emission spikes/drops > 2 sigma."""
        entries = self.db.query(EmissionEntry).filter(
            EmissionEntry.installation_id == installation_id,
            extract('year', EmissionEntry.date_start) == period_year
        ).order_by(EmissionEntry.date_start).all()
        
        if len(entries) < 3: return []
        
        values = [e.calculated_tco2 for e in entries]
        mean = np.mean(values)
        std_dev = np.std(values)
        
        anomalies = []
        for e in entries:
            val = e.calculated_tco2
            z_score = (val - mean) / std_dev if std_dev > 0 else 0
            
            if abs(z_score) > 2.0:
                anomalies.append({
                    "date": e.date_start.strftime("%Y-%m-%d"),
                    "value": val,
                    "z_score": round(z_score, 2),
                    "deviation_pct": round(((val - mean) / mean) * 100, 1),
                    "probable_cause": "Production surge" if z_score > 0 else "Shutdown/Maintenance",
                    "citation": "[AVR Article 15 - Data quality]"
                })
        
        return anomalies
