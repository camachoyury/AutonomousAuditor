import pytest
from decimal import Decimal

from ..core.exceptions import DocumentParseError
from ..services.document_service import DocumentService

def test_parse_pl_markdown(document_service: DocumentService, sample_pl_markdown: str):
    """Prueba el parseo de un P&L en formato Markdown."""
    result = document_service._parse_pl_markdown(sample_pl_markdown)
    
    assert result['period'] == '2024-Q1'
    assert len(result['revenue']) == 2
    assert len(result['expenses']) == 2
    assert len(result['totals']) == 3
    
    # Verificar ingresos
    revenue_names = {item.name for item in result['revenue']}
    assert 'Ventas' in revenue_names
    assert 'Otros' in revenue_names
    
    # Verificar gastos
    expense_names = {item.name for item in result['expenses']}
    assert 'Costos' in expense_names
    assert 'Gastos' in expense_names
    
    # Verificar totales
    assert result['totals']['Ingresos Totales'] == Decimal('1200')
    assert result['totals']['Gastos Totales'] == Decimal('800')
    assert result['totals']['Utilidad Neta'] == Decimal('400')

def test_parse_balance_markdown(document_service: DocumentService, sample_balance_markdown: str):
    """Prueba el parseo de un Balance en formato Markdown."""
    result = document_service._parse_balance_markdown(sample_balance_markdown)
    
    assert result['period'] == '2024-Q1'
    assert len(result['activos']) == 2
    assert len(result['pasivos']) == 2
    assert len(result['capital_contable']) == 2
    assert len(result['totals']) == 3
    
    # Verificar activos
    asset_names = {item.name for item in result['activos']}
    assert 'Efectivo' in asset_names
    assert 'Cuentas' in asset_names
    
    # Verificar pasivos
    liability_names = {item.name for item in result['pasivos']}
    assert 'Deudas' in liability_names
    assert 'Otros' in liability_names
    
    # Verificar capital contable
    equity_names = {item.name for item in result['capital_contable']}
    assert 'Capital' in equity_names
    assert 'Utilidad' in equity_names
    
    # Verificar totales
    assert result['totals']['Total Activos'] == Decimal('1500')
    assert result['totals']['Total Pasivos'] == Decimal('1000')
    assert result['totals']['Total Capital'] == Decimal('500')

def test_parse_invalid_markdown(document_service: DocumentService):
    """Prueba el manejo de errores con Markdown inválido."""
    invalid_content = """
    # Documento Inválido
    | Columna 1 | Columna 2 |
    |-----------|-----------|
    | Valor 1   | Valor 2   |
    """
    
    with pytest.raises(DocumentParseError):
        document_service._parse_pl_markdown(invalid_content)

def test_parse_document(document_service: DocumentService, sample_pl_document):
    """Prueba el parseo de un documento completo."""
    result = document_service.parse_document(sample_pl_document)
    
    assert result['period'] == '2024-Q1'
    assert len(result['revenue']) == 2
    assert len(result['expenses']) == 2
    assert len(result['totals']) == 3 