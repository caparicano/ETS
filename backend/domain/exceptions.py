
from backend.infrastructure.i18n import get_error_message

class DomainError(Exception):
    """Base class for domain logic errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class RegulatoryComplianceError(DomainError):
    """Raised when an operation violates MRR/AVR rules."""
    def __init__(self, detail: str):
        message = get_error_message("regulatory_error", detail=detail)
        super().__init__(message, code="REGULATORY_ERROR")

class CalculationError(DomainError):
    """Raised when the math engine fails or formula is invalid."""
    def __init__(self, detail: str):
        message = get_error_message("calculation_error", detail=detail)
        super().__init__(message, code="CALCULATION_ERROR")

class TenantAccessError(DomainError):
    """Raised on cross-organization access attempts."""
    def __init__(self):
        message = get_error_message("tenant_isolation")
        super().__init__(message, code="TENANT_ISOLATION_ERROR")

class WizardConfigurationError(DomainError):
    """Raised when the AI wizard generates invalid config."""
    pass
