import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from ..core.exceptions import ValidationError
from ..core.models import FinancialLineItem, FinancialDocument
from ..services.audit_service import AuditService
from ..services.document_service import DocumentService
from ..services.github_service import GitHubService

@pytest.fixture
def mock_document_service():
    """Fixture con un mock del servicio de documentos."""
    return Mock(spec=DocumentService)

@pytest.fixture
def mock_github_service():
    """Fixture con un mock del servicio de GitHub."""
    return Mock(spec=GitHubService)

@pytest.fixture
def audit_service(mock_document_service, mock_github_service):
    """Fixture con un servicio de auditoría."""
    return AuditService(
        document_service=mock_document_service,
        github_service=mock_github_service
    )

def test_compare_documents(audit_service):
    """Prueba la comparación de documentos financieros."""
    pl_data = {
        'period': '2024-Q1',
        'revenue': [],
        'expenses': [],
        'totals': {
            'Ingresos Totales': Decimal('1200'),
            'Gastos Totales': Decimal('800'),
            'Utilidad Neta': Decimal('400')
        }
    }
    
    balance_data = {
        'period': '2024-Q1',
        'activos': [],
        'pasivos': [],
        'capital_contable': [],
        'totals': {
            'Total Activos': Decimal('1500'),
            'Total Pasivos': Decimal('1000'),
            'Total Capital Contable': Decimal('500')
        }
    }
    
    discrepancies = audit_service.compare_documents(pl_data, balance_data)
    assert len(discrepancies) == 0

def test_period_mismatch(audit_service):
    """Prueba la detección de períodos diferentes."""
    pl_data = {
        'period': '2024-Q1',
        'totals': {}
    }
    
    balance_data = {
        'period': '2024-Q2',
        'totals': {}
    }
    
    discrepancies = audit_service.compare_documents(pl_data, balance_data)
    assert len(discrepancies) == 1
    assert discrepancies[0]['type'] == 'period_mismatch'

def test_income_mismatch(audit_service):
    """Prueba la detección de utilidad neta diferente."""
    pl_data = {
        'period': '2024-Q1',
        'totals': {
            'Utilidad Neta': Decimal('400')
        }
    }
    
    balance_data = {
        'period': '2024-Q1',
        'capital_contable': [
            FinancialLineItem(
                name='Utilidad',
                amount=Decimal('300'),
                category='equity',
                period='2024-Q1'
            )
        ],
        'totals': {}
    }
    
    discrepancies = audit_service.compare_documents(pl_data, balance_data)
    assert len(discrepancies) == 1
    assert discrepancies[0]['type'] == 'income_mismatch'

def test_unbalanced_balance(audit_service):
    """Prueba la detección de balance desbalanceado."""
    pl_data = {
        'period': '2024-Q1',
        'totals': {}
    }
    
    balance_data = {
        'period': '2024-Q1',
        'totals': {
            'Total Activos': Decimal('1500'),
            'Total Pasivos': Decimal('1000'),
            'Total Capital Contable': Decimal('400')  # Debería ser 500 para balancear
        }
    }
    
    discrepancies = audit_service.compare_documents(pl_data, balance_data)
    assert len(discrepancies) == 1
    assert discrepancies[0]['type'] == 'unbalanced'

def test_run_audit(audit_service):
    """Prueba la ejecución completa de una auditoría."""
    # Configurar mocks
    pl_doc = FinancialDocument(content='', doc_type='pl', file_format='markdown')
    balance_doc = FinancialDocument(content='', doc_type='balance', file_format='markdown')
    
    audit_service.github_service.retrieve_documents.return_value = {
        'pl': pl_doc,
        'balance': balance_doc
    }
    
    audit_service.document_service.parse_document.side_effect = [
        {
            'period': '2024-Q1',
            'totals': {'Utilidad Neta': Decimal('400')}
        },
        {
            'period': '2024-Q1',
            'totals': {
                'Total Activos': Decimal('1500'),
                'Total Pasivos': Decimal('1000'),
                'Total Capital Contable': Decimal('500')
            }
        }
    ]
    
    audit_service.github_service.create_or_update_issue.return_value = 'https://github.com/owner/repo/issues/1'
    
    # Ejecutar auditoría
    result = audit_service.run_audit('https://github.com/owner/repo')
    
    assert result.status == 'success'
    assert len(result.discrepancies) == 0
    assert result.issue_url is None 