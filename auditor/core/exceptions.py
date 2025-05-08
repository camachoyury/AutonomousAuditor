class FinancialAuditError(Exception):
    """Excepción base para errores de auditoría financiera."""
    pass

class DocumentParseError(FinancialAuditError):
    """Error al parsear un documento financiero."""
    pass

class GitHubError(FinancialAuditError):
    """Error en la interacción con GitHub."""
    pass

class ValidationError(FinancialAuditError):
    """Error de validación en los datos financieros."""
    pass

class ConfigurationError(FinancialAuditError):
    """Error en la configuración del sistema."""
    pass 