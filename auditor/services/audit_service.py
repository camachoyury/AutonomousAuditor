import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from ..core.models import AuditResult
from ..core.constants import TOLERANCE
from ..core.exceptions import LLMError
from .document_service import DocumentService
from .github_service import GitHubService
from .llm_service import LLMAuditService

logger = logging.getLogger(__name__)


class AuditService:
    """Orquesta la auditoría: recuperar -> parsear -> reglas -> Gemini -> reportar."""

    def __init__(
        self,
        document_service: Optional[DocumentService] = None,
        github_service: Optional[GitHubService] = None,
        llm_service: Optional[LLMAuditService] = None,
    ):
        self.document_service = document_service or DocumentService()
        self._github_service = github_service
        self.llm_service = llm_service or LLMAuditService()

    @property
    def github_service(self) -> GitHubService:
        """Se crea bajo demanda: el análisis local (demo) no necesita token de GitHub."""
        if self._github_service is None:
            self._github_service = GitHubService()
        return self._github_service

    def analyze(self, pl_data: Dict, balance_data: Dict) -> Tuple[List[Dict], bool, Optional[str]]:
        """Reglas deterministas + revisión con Gemini.

        Devuelve (discrepancias, gemini_usado, error_de_gemini). Si Gemini falla,
        se conservan los hallazgos de las reglas.
        """
        discrepancies = self.compare_documents(pl_data, balance_data)
        if not self.llm_service.enabled:
            return discrepancies, False, None
        try:
            discrepancies += self.llm_service.review(pl_data, balance_data, discrepancies)
            return discrepancies, True, None
        except LLMError as exc:
            logger.warning("Se omite el análisis con Gemini: %s", exc)
            return discrepancies, False, str(exc)

    def run_audit(self, repo_url: str, branch: str = "main") -> AuditResult:
        """Ejecuta una auditoría completa sobre un repo de GitHub y reporta en un Issue."""
        try:
            docs = self.github_service.retrieve_documents(repo_url, branch)
            pl_data = self.document_service.parse_document(docs['pl'])
            balance_data = self.document_service.parse_document(docs['balance'])

            discrepancies, llm_used, llm_error = self.analyze(pl_data, balance_data)

            issue_url = None
            if discrepancies:
                issue_url = self.github_service.create_or_update_issue(
                    discrepancies, repo_url, period=pl_data.get('period')
                )

            return AuditResult(
                status="success",
                discrepancies=discrepancies,
                issue_url=issue_url,
                llm_used=llm_used,
                llm_error=llm_error,
            )

        except Exception as e:
            logger.exception("Falló la auditoría de %s", repo_url)
            return AuditResult(status="error", discrepancies=[], error_message=str(e))

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
        
        for d in discrepancies:
            d.setdefault('source', 'rules')
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
