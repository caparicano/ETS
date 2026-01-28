
import os
import google.generativeai as genai
from typing import Optional, List

class OCRService:
    def __init__(self):
        api_key = os.getenv("API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    def extract_text(self, file_bytes: bytes, mime_type: str) -> str:
        """
        Extract text from image or PDF using Gemini Multimodal capabilities.
        """
        if not self.model:
            return "OCR Service Unavailable (No API Key)"
            
        prompt = "Extract all text from this document verbatim. Return only the extracted text, no markdown."
        
        try:
            response = self.model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": file_bytes}
            ])
            return response.text
        except Exception as e:
            print(f"OCR Failed: {e}")
            return ""

    def validate_content(self, text: str, must_contain: List[str]) -> bool:
        """
        Returns True if all keywords are present in the extracted text.
        Case insensitive.
        """
        if not must_contain:
            return True
            
        lower_text = text.lower()
        for keyword in must_contain:
            if keyword.lower() not in lower_text:
                return False
        return True
