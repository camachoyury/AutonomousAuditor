from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass

from ..core.models import FinancialDocument, AuditResult
from ..core.exceptions import ValidationError
from ..core.constants import TOLERANCE
from .document_service import DocumentService
from .github_service import GitHubService

@dataclass
class AuditResult:
    """Resultado de una auditoría."""
    status: str
    discrepancies: List[Dict]
    issue_url: Optional[str] = None

class AuditService:
    """Servicio para realizar auditorías financieras."""

    def __init__(self, document_service: Optional[DocumentService] = None, github_service: Optional[GitHubService] = None):
        """Inicializa el servicio de auditoría."""
        self.document_service = document_service or DocumentService()
        self.github_service = github_service or GitHubService()

    def run_audit(self, repo_url: str, branch: str = "main") -> AuditResult:
        """Ejecuta una auditoría financiera completa."""
        try:
            # 1. Recuperar documentos
            docs = self.github_service.retrieve_documents(repo_url, branch)
            
            # 2. Parsear documentos
            pl_data = self.document_service.parse_document(docs['pl'])
            balance_data = self.document_service.parse_document(docs['balance'])
            
            # 3. Comparar documentos
            discrepancies = self.compare_documents(pl_data, balance_data)
            
            # 4. Crear/actualizar issue
            issue_url = None
            if discrepancies:
                issue_url = self.github_service.create_or_update_issue(discrepancies, repo_url)
            
            return AuditResult(
                status="success",
                discrepancies=discrepancies,
                issue_url=issue_url
            )
            
        except Exception as e:
            return AuditResult(
                status="error",
                discrepancies=[{
                    'type': 'system_error',
                    'description': str(e),
                    'severity': 'high',
                    'fix': 'Contacta al equipo de soporte'
                }],
                issue_url=None
            )

    def compare_documents(self, pl_data: Dict, balance_data: Dict) -> List[Dict]:
        """Compara los documentos financieros y detecta inconsistencias."""
        discrepancies = []
        
        # Verificar que los períodos coincidan
        if pl_data.get('period') != balance_data.get('period'):
            discrepancies.append({
                'type': 'period_mismatch',
                'description': f"Los períodos no coinciden: P&L ({pl_data.get('period')}) vs Balance ({balance_data.get('period')})",
                'severity': 'high',
                'fix': 'Asegurarse de que ambos documentos correspondan al mismo período contable.'
            })
        
        # Verificar que la utilidad neta coincida con la utilidad del período en el balance
        pl_net_income = self._find_net_income(pl_data)
        balance_net_income = self._find_net_income(balance_data)
        
        if pl_net_income is not None and balance_net_income is not None:
            if abs(pl_net_income - balance_net_income) > TOLERANCE:
                discrepancies.append({
                    'type': 'income_mismatch',
                    'description': f"La utilidad neta no coincide: P&L (${pl_net_income}) vs Balance (${balance_net_income})",
                    'severity': 'high',
                    'fix': f"Ajustar la utilidad neta en el Balance General para que coincida con el P&L: ${pl_net_income}"
                })
        
        # Verificar cambios en ganancias retenidas
        retained_earnings = self._find_retained_earnings(balance_data)
        if retained_earnings is not None and pl_net_income is not None:
            expected_retained_earnings = retained_earnings + pl_net_income
            if abs(expected_retained_earnings - retained_earnings) > TOLERANCE:
                discrepancies.append({
                    'type': 'retained_earnings_mismatch',
                    'description': f"Las ganancias retenidas no reflejan la utilidad del período. Actual: ${retained_earnings}, Esperado: ${expected_retained_earnings}",
                    'severity': 'high',
                    'fix': f"Ajustar las ganancias retenidas para incluir la utilidad del período: ${expected_retained_earnings}"
                })
        
        # Verificar que los totales sean consistentes
        pl_totals = pl_data.get('totals', {})
        balance_totals = balance_data.get('totals', {})
        
        # Verificar que los ingresos totales sean razonables en comparación con los activos
        if 'Ingresos Totales' in pl_totals and 'Total Activos' in balance_totals:
            revenue = pl_totals['Ingresos Totales']
            assets = balance_totals['Total Activos']
            if revenue > assets * Decimal('2'):
                discrepancies.append({
                    'type': 'unusual_ratio',
                    'description': f"Los ingresos (${revenue}) son inusualmente altos en comparación con los activos (${assets})",
                    'severity': 'medium',
                    'fix': 'Verificar que todos los activos estén correctamente registrados y valorados.'
                })
        
        # Verificar que los gastos totales sean razonables en comparación con los ingresos
        if 'Gastos Totales' in pl_totals and 'Ingresos Totales' in pl_totals:
            expenses = pl_totals['Gastos Totales']
            revenue = pl_totals['Ingresos Totales']
            if expenses > revenue:
                discrepancies.append({
                    'type': 'expense_ratio',
                    'description': f"Los gastos (${expenses}) son mayores que los ingresos (${revenue})",
                    'severity': 'high',
                    'fix': 'Revisar y validar todos los gastos registrados. Verificar si hay gastos duplicados o incorrectamente clasificados.'
                })
        
        # Verificar que el balance esté balanceado
        if 'Total Activos' in balance_totals and 'Total Pasivos' in balance_totals and 'Total Capital Contable' in balance_totals:
            assets = balance_totals['Total Activos']
            liabilities = balance_totals['Total Pasivos']
            equity = balance_totals['Total Capital Contable']
            
            if abs(assets - (liabilities + equity)) > TOLERANCE:
                discrepancies.append({
                    'type': 'unbalanced',
                    'description': f"El balance no está balanceado: Activos (${assets}) ≠ Pasivos (${liabilities}) + Capital (${equity})",
                    'severity': 'high',
                    'fix': f"Ajustar las cuentas para mantener la ecuación contable: A = P + C. Diferencia actual: ${abs(assets - (liabilities + equity))}"
                })
        
        return discrepancies

    def _find_net_income(self, data: Dict) -> Optional[Decimal]:
        """Busca la utilidad neta en los datos."""
        # Buscar en totales
        for name, amount in data.get('totals', {}).items():
            if 'utilidad' in name.lower() or 'net' in name.lower():
                return amount
        
        # Buscar en capital contable
        for item in data.get('capital_contable', []):
            if 'utilidad' in item.name.lower() or 'net' in item.name.lower():
                return item.amount
        
        return None

    def _find_retained_earnings(self, data: Dict) -> Optional[Decimal]:
        """Busca las ganancias retenidas en los datos."""
        for item in data.get('capital_contable', []):
            if 'retenidas' in item.name.lower() or 'retained' in item.name.lower():
                return item.amount
        return None 