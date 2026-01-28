
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class APADocumentType(str, Enum):
    # Core APA Submissions (Official)
    RELATORIO_EMISSOES = "relatorio_emissoes"  # RE - Annual Emissions Report
    PARECER_VERIFICACAO = "parecer_verificacao"  # Verification Opinion
    RELATORIO_NIVEL_ATIVIDADE = "relatorio_nivel_atividade"  # ALC
    RELATORIO_MELHORIA = "relatorio_melhoria"  # Improvement Report
    
    # Evidence Documents (Ceramic)
    FATURAS_GAS_NATURAL = "faturas_gas_natural"
    ANALISE_CARBONATOS_ARGILA = "analise_carbonatos_argila"
    CERTIFICADO_CALIBRACAO_BALANCA = "certificado_calibracao_balanca"
    CERTIFICADO_LABORATORIO_ISO17025 = "certificado_laboratorio_iso17025"
    
    # Evidence Documents (Tomato/Agri-food)
    CERTIFICADO_SUSTENTABILIDADE_BIOMASSA = "certificado_sustentabilidade_biomassa"
    REGISTOS_EFICIENCIA_CHP = "registos_eficiencia_chp"
    CALIBRACAO_CONTADOR_VAPOR = "calibracao_contador_vapor"

class DocumentRule(BaseModel):
    allowed_formats: List[str]
    max_size_mb: int
    requires_digital_signature: bool
    mandatory_fields: List[str]
    description_pt: str

# Configuration Rules strictly following APA/SILiAmb requirements
APA_DOCUMENT_RULES: Dict[APADocumentType, DocumentRule] = {
    APADocumentType.RELATORIO_EMISSOES: DocumentRule(
        allowed_formats=[".pdf", ".xml"],
        max_size_mb=50,
        requires_digital_signature=True,
        mandatory_fields=["installation_id", "reporting_year", "verifier_id"],
        description_pt="Relatório de Emissões (RE) submetido no SILiAmb"
    ),
    APADocumentType.PARECER_VERIFICACAO: DocumentRule(
        allowed_formats=[".pdf"],
        max_size_mb=20,
        requires_digital_signature=True,
        mandatory_fields=["verifier_accreditation", "opinion_statement"],
        description_pt="Parecer de Verificação emitido por verificador acreditado (ex: APCER)"
    ),
    APADocumentType.FATURAS_GAS_NATURAL: DocumentRule(
        allowed_formats=[".pdf", ".xlsx", ".csv"],
        max_size_mb=10,
        requires_digital_signature=False,
        mandatory_fields=["supplier_name", "consumption_mwh", "invoice_period"],
        description_pt="Faturas de Gás Natural (Comprovativo de Atividade)"
    ),
    APADocumentType.ANALISE_CARBONATOS_ARGILA: DocumentRule(
        allowed_formats=[".pdf"],
        max_size_mb=5,
        requires_digital_signature=False,
        mandatory_fields=["caco3_percentage", "sample_id", "analysis_date"],
        description_pt="Boletim de Análise Laboratorial (ISO 17025)"
    ),
    APADocumentType.CERTIFICADO_SUSTENTABILIDADE_BIOMASSA: DocumentRule(
        allowed_formats=[".pdf"],
        max_size_mb=10,
        requires_digital_signature=True,
        mandatory_fields=["certificate_id", "biomass_type", "red_ii_compliance"],
        description_pt="Comprovativo de Sustentabilidade (RED II)"
    ),
    APADocumentType.CALIBRACAO_CONTADOR_VAPOR: DocumentRule(
        allowed_formats=[".pdf"],
        max_size_mb=3,
        requires_digital_signature=False,
        mandatory_fields=["steam_meter_id", "calibration_date", "next_calibration_date"],
        description_pt="Certificado de Calibração de Contador de Vapor"
    )
}

# Defaults for types not explicitly listed
DEFAULT_RULE = DocumentRule(
    allowed_formats=[".pdf", ".jpg", ".png", ".xlsx"],
    max_size_mb=10,
    requires_digital_signature=False,
    mandatory_fields=[],
    description_pt="Documento Genérico"
)

def get_rule_for_type(doc_type: APADocumentType) -> DocumentRule:
    return APA_DOCUMENT_RULES.get(doc_type, DEFAULT_RULE)
