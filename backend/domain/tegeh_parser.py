
import io
import json
import os
from pypdf import PdfReader
import google.generativeai as genai
from typing import Dict, Any, List
from pydantic import BaseModel

class ParsedEquipment(BaseModel):
    name: str
    type: str # "Kiln", "Boiler", "Dryer"
    fuel_guess: str # "Natural Gas", "Biomass"

class TEGEHData(BaseModel):
    installation_name: str
    permit_id: str
    address: str
    equipment: List[ParsedEquipment]

class TEGEHParser:
    def __init__(self):
        # Initialize Gemini
        api_key = os.getenv("API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp') # Or generic flash
        else:
            self.model = None

    def parse_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        1. Extract text from PDF.
        2. Send to LLM for structured extraction.
        """
        text = self._extract_text(file_bytes)
        
        if not self.model:
            # Fallback for dev/test without API key
            return self._mock_extraction()

        return self._extract_with_llm(text)

    def _extract_text(self, file_bytes: bytes) -> str:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text[:10000] # Truncate to avoid context limits if huge

    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        prompt = f"""
        You are an expert environmental engineer. Extract the following information from the TEGEH Permit text below.
        Return ONLY valid JSON.
        
        Fields required:
        - installation_name
        - permit_id (TEGEH number)
        - address
        - equipment: list of objects {{"name": "...", "type": "Kiln/Dryer/Boiler", "fuel_guess": "..."}}
        
        Text:
        {text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Simple cleanup of markdown code blocks
            json_str = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(json_str)
        except Exception as e:
            print(f"LLM Parsing failed: {e}")
            return self._mock_extraction()

    def _mock_extraction(self) -> Dict[str, Any]:
        return {
            "installation_name": "Fábrica Cerâmica Modelo (Mock)",
            "permit_id": "TEGEH-2024-MOCK",
            "address": "Zona Industrial de Leiria",
            "equipment": [
                {"name": "Forno Túnel 1", "type": "Kiln", "fuel_guess": "Natural Gas"},
                {"name": "Secador 1", "type": "Dryer", "fuel_guess": "Natural Gas"}
            ]
        }
