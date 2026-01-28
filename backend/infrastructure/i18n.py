
"""Internationalization for Portuguese error messages."""

ERROR_MESSAGES_PT = {
    "validation_error": "Erro de validação: {detail}",
    "not_found": "Recurso não encontrado: {resource}",
    "calculation_error": "Erro no cálculo de emissões: {detail}",
    "regulatory_error": "Erro de conformidade regulamentar: {detail}",
    "negative_value": "Valor não pode ser negativo: {field}",
    "missing_factor": "Fator de emissão não encontrado para {fuel_type} em {date}",
    "invalid_tier": "Tier {tier} não é válido para fonte {source_type}. MRR requer Tier {min_tier} mínimo.",
    "missing_evidence": "Evidência documental em falta: {document_type}",
    "unauthorized": "Sem autorização para aceder a este recurso",
    "deadline_passed": "Prazo ultrapassado: {task_name} devia ter sido submetido a {deadline}",
    "tenant_isolation": "Acesso negado: Recurso pertence a outra organização."
}

def get_error_message(error_code: str, **kwargs) -> str:
    """Get localized error message in Portuguese."""
    template = ERROR_MESSAGES_PT.get(error_code, "Erro desconhecido")
    return template.format(**kwargs)
