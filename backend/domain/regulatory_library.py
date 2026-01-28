
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import math
import json
from datetime import date
from backend.infrastructure.models import RegulatoryDocument, RegulatoryChunk

class RegulatoryLibraryService:
    """
    Manages the knowledge base of EU ETS regulations.
    Implements a pure-python cosine similarity search to work without pgvector extension
    in constrained environments, while maintaining the interface for future upgrade.
    """
    
    def __init__(self, db: Session):
        self.db = db

    def ingest_document(self, title: str, short_code: str, doc_type: str, pub_date: date, chunks: List[Dict[str, Any]]):
        """
        Save a document and its vectorized chunks.
        chunks: List of dicts with keys: {'article_reference', 'content', 'embedding'}
        """
        # Check if exists
        existing = self.db.query(RegulatoryDocument).filter_by(short_code=short_code).first()
        if existing:
            return existing

        doc = RegulatoryDocument(
            title=title,
            short_code=short_code,
            doc_type=doc_type,
            publication_date=pub_date
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        for chunk_data in chunks:
            chunk = RegulatoryChunk(
                document_id=doc.id,
                article_reference=chunk_data['article_reference'],
                content=chunk_data['content'],
                embedding=chunk_data['embedding'] # List[float]
            )
            self.db.add(chunk)
        
        self.db.commit()
        return doc

    def search(self, query_embedding: List[float], limit: int = 5, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Semantic search using Cosine Similarity.
        Retrieves all chunks (cached/efficiently) and computes similarity in-memory.
        Note: For production with millions of chunks, replace this with DB-native vector search.
        """
        # 1. Fetch all chunks (Optimization: Cache this or use specific DB query)
        # In this specific app scale (ETS regulations), we talk about ~5000 chunks max, fits in memory.
        all_chunks = self.db.query(RegulatoryChunk).join(RegulatoryDocument).all()
        
        results = []
        
        for chunk in all_chunks:
            if not chunk.embedding:
                continue
                
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            
            if score >= min_score:
                results.append({
                    "score": score,
                    "doc_title": chunk.document.title,
                    "short_code": chunk.document.short_code,
                    "article": chunk.article_reference,
                    "content": chunk.content
                })
        
        # Sort desc by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(a * a for a in v1))
        magnitude_v2 = math.sqrt(sum(b * b for b in v2))
        
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
            
        return dot_product / (magnitude_v1 * magnitude_v2)
