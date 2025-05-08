import pytest
from decimal import Decimal
from typing import Dict, List

from ..core.models import FinancialDocument, FinancialLineItem
from ..services.document_service import DocumentService
from ..services.github_service import GitHubService
from ..services.audit_service import AuditService

@pytest.fixture
def sample_pl_markdown() -> str:
    """Fixture con un ejemplo de P&L en formato Markdown."""
    return """
    # Estado de Resultados
    Periodo: 2024-Q1

    ## Ingresos
    | Concepto | Monto |
    |----------|-------|
    | Ventas   | $1000 |
    | Otros    | $200  |

    ## Gastos
    | Concepto | Monto |
    |----------|-------|
    | Costos   | $500  |
    | Gastos   | $300  |

    ## Totales
    | Concepto | Monto |
    |----------|-------|
    | Ingresos Totales | $1200 |
    | Gastos Totales   | $800  |
    | Utilidad Neta    | $400  |
    """

@pytest.fixture
def sample_balance_markdown() -> str:
    """Fixture con un ejemplo de Balance en formato Markdown."""
    return """
    # Balance General
    Periodo: 2024-Q1

    ## Activos
    | Concepto | Monto |
    |----------|-------|
    | Efectivo | $1000 |
    | Cuentas  | $500  |

    ## Pasivos
    | Concepto | Monto |
    |----------|-------|
    | Deudas   | $800  |
    | Otros    | $200  |

    ## Capital Contable
    | Concepto | Monto |
    |----------|-------|
    | Capital  | $300  |
    | Utilidad | $200  |

    ## Totales
    | Concepto | Monto |
    |----------|-------|
    | Total Activos | $1500 |
    | Total Pasivos | $1000 |
    | Total Capital | $500  |
    """

@pytest.fixture
def sample_pl_document(sample_pl_markdown: str) -> FinancialDocument:
    """Fixture con un documento de P&L."""
    return FinancialDocument(
        content=sample_pl_markdown,
        doc_type='pl',
        file_format='markdown'
    )

@pytest.fixture
def sample_balance_document(sample_balance_markdown: str) -> FinancialDocument:
    """Fixture con un documento de Balance."""
    return FinancialDocument(
        content=sample_balance_markdown,
        doc_type='balance',
        file_format='markdown'
    )

@pytest.fixture
def document_service() -> DocumentService:
    """Fixture con el servicio de documentos."""
    return DocumentService()

@pytest.fixture
def github_service() -> GitHubService:
    """Fixture con el servicio de GitHub."""
    return GitHubService()

@pytest.fixture
def audit_service(document_service: DocumentService, github_service: GitHubService) -> AuditService:
    """Fixture con el servicio de auditoría."""
    return AuditService(document_service, github_service) 