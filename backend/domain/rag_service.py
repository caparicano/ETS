
import os
import google.generativeai as genai
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.domain.regulatory_library import RegulatoryLibraryService
from backend.infrastructure.models import AdvisorySession, AdvisoryMessage, Installation

class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.library = RegulatoryLibraryService(db)
        
        api_key = os.getenv("API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.embed_model = 'models/text-embedding-004'
        else:
            self.model = None

    def create_session(self, user_id: int, context: Dict[str, Any] = {}) -> str:
        """Start a new advisory session."""
        import uuid
        session_id = str(uuid.uuid4())
        session = AdvisorySession(
            id=session_id,
            user_id=user_id,
            title="New Consultation",
            context_data=context
        )
        self.db.add(session)
        self.db.commit()
        return session_id

    def ask(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Main RAG Pipeline:
        1. Embed Query
        2. Retrieve Context (Regulations)
        3. Retrieve Installation Context (DB Data)
        4. Synthesize Answer with Citations
        """
        session = self.db.query(AdvisorySession).get(session_id)
        if not session:
            raise ValueError("Session not found")

        # 1. Embed
        query_embedding = self._get_embedding(query)
        
        # 2. Retrieve Regulatory Context
        citations = []
        context_text = ""
        if query_embedding:
            results = self.library.search(query_embedding, limit=4)
            for r in results:
                citations.append({
                    "doc": r['short_code'],
                    "article": r['article'],
                    "snippet": r['content'][:150] + "...",
                    "relevance": round(r['score'], 2)
                })
                context_text += f"SOURCE [{r['short_code']} {r['article']}]: {r['content']}\n\n"
        
        # 3. Installation Context (if relevant)
        inst_context = self._get_installation_context(session.context_data.get('installation_id'))
        
        # 4. Prompt Engineering
        system_prompt = f"""
        You are CeramETS, an expert EU ETS Compliance Consultant.
        
        RULES:
        1. Base your answer PRIMARILY on the provided SOURCES.
        2. ALWAYS cite your sources using the format [Document Article].
        3. If the user asks about their specific data, use the INSTALLATION DATA provided.
        4. If the Sources do not contain the answer, state that you are unsure and recommend checking the text directly.
        5. Be concise and professional.
        
        INSTALLATION DATA:
        {inst_context}
        
        REGULATORY SOURCES:
        {context_text}
        """
        
        # 5. Generate
        full_response = self._generate_llm_response(system_prompt, query)
        
        # 6. Save History
        user_msg = AdvisoryMessage(session_id=session_id, role="user", content=query)
        ai_msg = AdvisoryMessage(session_id=session_id, role="model", content=full_response, citations=citations)
        
        self.db.add(user_msg)
        self.db.add(ai_msg)
        self.db.commit()
        
        return {
            "answer": full_response,
            "citations": citations
        }

    def _get_embedding(self, text: str) -> List[float]:
        if not self.model: return [0.0] * 768 # Mock
        try:
            result = genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding failed: {e}")
            return []

    def _generate_llm_response(self, system_prompt: str, user_query: str) -> str:
        if not self.model: return "AI Service Unavailable (Missing API Key)."
        try:
            chat = self.model.start_chat(history=[
                {"role": "user", "parts": system_prompt},
                {"role": "model", "parts": "Understood. I am ready to act as the Consultant."}
            ])
            response = chat.send_message(user_query)
            return response.text
        except Exception as e:
            return f"Error generating advice: {str(e)}"

    def _get_installation_context(self, installation_id: int) -> str:
        if not installation_id: return "No specific installation selected."
        
        inst = self.db.query(Installation).get(installation_id)
        if not inst: return "Installation not found."
        
        # Build summary of streams and last emissions
        summary = f"Installation: {inst.name} (Permit: {inst.permit_id})\n"
        summary += "Source Streams:\n"
        for s in inst.source_streams:
            summary += f"- {s.name} ({s.fuel_or_material}, Tier {s.tier})\n"
            
        return summary
