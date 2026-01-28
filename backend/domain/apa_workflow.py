
"""APA Portugal specific compliance workflow.

This module handles the complete submission cycle:
1. Relatório de Emissões (RE) - Annual Emissions Report
2. Parecer de Verificação - Verification Opinion  
3. Relatório de Nível de Atividade (ALC) - Activity Level Report
4. Relatório de Melhoria - Improvement Report
5. RPLE Surrender - Allowance surrender

All submissions go through SILiAmb platform.
"""

from datetime import date, datetime
from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import extract
from backend.infrastructure.models import EmissionEntry, Document, Installation, SectorType

class APADocumentType(str, Enum):
    """APA Portugal required document types."""
    RELATORIO_EMISSOES = "relatorio_emissoes"  # RE - Due March 31
    PARECER_VERIFICACAO = "parecer_verificacao"  # Verification - Due March 15
    RELATORIO_NIVEL_ATIVIDADE = "relatorio_nivel_atividade"  # ALC - Due March 31
    RELATORIO_MELHORIA = "relatorio_melhoria"  # Improvement - Due June 30
    RPLE_SURRENDER = "rple_surrender"  # Allowance surrender - Due April 30
    
    # Evidence documents
    FATURAS_GAS_NATURAL = "faturas_gas_natural"
    ANALISE_CARBONATOS = "analise_carbonatos_argila"
    CERTIFICADO_CALIBRACAO = "certificado_calibracao_balanca"
    CERTIFICADO_LABORATORIO = "certificado_laboratorio_iso17025"

class APASubmissionStatus(str, Enum):
    """Status of APA submission."""
    DRAFT = "draft"  # Being prepared
    READY_FOR_VERIFICATION = "ready_for_verification"  # Ready for verifier
    VERIFIED = "verified"  # Verifier approved
    SUBMITTED_TO_APA = "submitted_to_apa"  # Submitted via SILiAmb
    ACCEPTED_BY_APA = "accepted_by_apa"  # APA confirmed receipt
    REJECTED_BY_APA = "rejected_by_apa"  # APA rejected - needs correction

class APAWorkflowService:
    """Service to manage APA Portugal compliance workflow."""
    
    def __init__(self, db: Session):
        self.db = db

    def check_submission_readiness(
        self, 
        installation_id: int,
        reporting_year: int,
        document_type: APADocumentType
    ) -> Dict[str, any]:
        """
        Check if installation is ready to submit document to APA.
        
        Returns:
            Dict with:
            - ready: bool
            - missing_documents: List[str]
            - missing_data: List[str]
            - warnings: List[str]
        """
        
        if document_type == APADocumentType.RELATORIO_EMISSOES:
            return self._check_re_readiness(installation_id, reporting_year)
        elif document_type == APADocumentType.PARECER_VERIFICACAO:
            # Verification readiness logic could go here
            return {"ready": True, "missing_documents": [], "missing_data": [], "warnings": []}
            
        return {"ready": False, "missing_documents": ["Unknown document type"], "missing_data": [], "warnings": []}
    
    def _check_re_readiness(self, installation_id: int, year: int) -> Dict:
        """Check if RE (Annual Emissions Report) is ready for submission.
        
        APA Requirements:
        - All 12 months of emission data entered
        - All fuel invoices uploaded
        - For ceramics: Quarterly lab analysis for CaCO3
        - Weighbridge calibration certificate (if using mass balance)
        - Verification Opinion attached
        - No data gaps or anomalies
        """
        missing_docs = []
        missing_data = []
        warnings = []
        
        installation = self.db.query(Installation).get(installation_id)
        if not installation:
             return {"ready": False, "error": "Installation not found"}

        # Check monthly data completeness
        # Count unique months with entries
        entries = self.db.query(EmissionEntry).filter(
            EmissionEntry.installation_id == installation_id,
            extract('year', EmissionEntry.date_start) == year
        ).all()
        
        months_covered = set()
        for entry in entries:
            months_covered.add(entry.date_start.month)
            
        if len(months_covered) < 12:
            missing_data.append(f"Dados mensais em falta: {12 - len(months_covered)} meses detetados")
        
        # Check required documents
        documents = self.db.query(Document).filter(
            Document.installation_id == installation_id,
            Document.reporting_year == year
        ).all()
        
        doc_types_present = {doc.document_type for doc in documents}
        
        # Ceramic industry specific
        if installation.organization.sector == SectorType.CERAMIC:
            if APADocumentType.ANALISE_CARBONATOS.value not in doc_types_present:
                missing_docs.append("Análise laboratorial de carbonatos (ISO 17025)")
            if APADocumentType.CERTIFICADO_CALIBRACAO.value not in doc_types_present:
                warnings.append("Certificado de calibração de balança recomendado")
        
        # All industries
        if APADocumentType.FATURAS_GAS_NATURAL.value not in doc_types_present:
            missing_docs.append("Faturas de gás natural")
        
        if APADocumentType.PARECER_VERIFICACAO.value not in doc_types_present:
            missing_docs.append("Parecer de Verificação (obrigatório antes de submeter RE)")
        
        return {
            "ready": len(missing_docs) == 0 and len(missing_data) == 0,
            "missing_documents": missing_docs,
            "missing_data": missing_data,
            "warnings": warnings
        }
    
    def generate_re_xml(self, installation_id: int, year: int) -> str:
        """Generate Relatório de Emissões in XML format for SILiAmb."""
        # Implementation placeholder
        return "<xml>SiliamB RE Export</xml>"
    
    def generate_re_pdf(self, installation_id: int, year: int) -> bytes:
        """Generate RE in PDF format with APA required structure."""
        # Implementation placeholder
        return b"%PDF-1.4..."
