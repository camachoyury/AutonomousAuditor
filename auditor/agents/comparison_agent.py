from google.adk.tools.function_tool import FunctionTool as Tool
from google.adk.agents import Agent
from typing import Dict, List, Optional
from decimal import Decimal
from auditor.core.prompts import COMPARISON_PROMPTS, ANALYSIS_PROMPTS

class ComparisonAgent:
    def __init__(self):
        self.agent = Agent(
            name="comparison_agent",
            model="gemini-2.0-flash",
            description="Agente para comparar documentos financieros",
            tools=[Tool(self.compare_documents)]
        )
    
    def compare_documents(self, pl_doc, balance_doc):
        """Compara dos documentos financieros y detecta discrepancias."""
        try:
            # Parsear documentos
            pl_data = pl_doc.parse()
            balance_data = balance_doc.parse()
            
            discrepancies = []
            
            # Verificar períodos
            if pl_data['period'] != balance_data['period']:
                discrepancies.append({
                    'type': 'period_mismatch',
                    'description': f"Los períodos no coinciden: P&L ({pl_data['period']}) vs Balance ({balance_data['period']})",
                    'severity': 'high'
                })
            
            # Verificar utilidad neta
            pl_net_income = pl_data['totals'].get('Utilidad Neta')
            balance_net_income = None
            for item in balance_data['capital_contable']:
                if 'utilidad' in item.name.lower():
                    balance_net_income = item.amount
                    break
            
            if pl_net_income and balance_net_income and pl_net_income != balance_net_income:
                discrepancies.append({
                    'type': 'net_income_mismatch',
                    'description': f"La utilidad neta no coincide: P&L (${pl_net_income}) vs Balance (${balance_net_income})",
                    'severity': 'high'
                })
            
            return discrepancies
            
        except Exception as e:
            return [{
                'type': 'error',
                'description': f"Error al comparar documentos: {str(e)}",
                'severity': 'high'
            }]
    
    @Tool
    def compare_documents_old(self, pl_data: Dict, balance_data: Dict) -> List[Dict]:
        """Compara los documentos financieros y detecta inconsistencias."""
        discrepancies = []
        
        # Verificar que los períodos coincidan
        if pl_data.get('period') != balance_data.get('period'):
            prompt = COMPARISON_PROMPTS['period_match'].format(
                pl_period=pl_data.get('period'),
                balance_period=balance_data.get('period')
            )
            discrepancies.append({
                'type': 'period_mismatch',
                'description': f"Los períodos no coinciden: P&L ({pl_data.get('period')}) vs Balance ({balance_data.get('period')})",
                'severity': 'high',
                'fix': 'Asegurarse de que ambos documentos correspondan al mismo período contable.',
                'prompt_used': prompt
            })
        
        # Verificar que la utilidad neta coincida
        pl_net_income = self._find_net_income(pl_data)
        balance_net_income = self._find_net_income(balance_data)
        
        if pl_net_income is not None and balance_net_income is not None:
            prompt = COMPARISON_PROMPTS['net_income'].format(
                pl_net_income=pl_net_income,
                balance_net_income=balance_net_income,
                tolerance=Decimal('0.01')
            )
            if abs(pl_net_income - balance_net_income) > Decimal('0.01'):
                discrepancies.append({
                    'type': 'income_mismatch',
                    'description': f"La utilidad neta no coincide: P&L (${pl_net_income}) vs Balance (${balance_net_income})",
                    'severity': 'high',
                    'fix': f"Ajustar la utilidad neta en el Balance General para que coincida con el P&L: ${pl_net_income}",
                    'prompt_used': prompt
                })
        
        # Verificar ratios y ecuaciones
        pl_totals = pl_data.get('totals', {})
        balance_totals = balance_data.get('totals', {})
        
        # Ratio ingresos/activos
        if 'Ingresos Totales' in pl_totals and 'Total Activos' in balance_totals:
            revenue = pl_totals['Ingresos Totales']
            assets = balance_totals['Total Activos']
            ratio = revenue / assets if assets != 0 else 0
            
            prompt = ANALYSIS_PROMPTS['revenue_assets_ratio'].format(
                revenue=revenue,
                assets=assets,
                ratio=ratio
            )
            
            if ratio > 2:
                discrepancies.append({
                    'type': 'unusual_ratio',
                    'description': f"Los ingresos (${revenue}) son inusualmente altos en comparación con los activos (${assets})",
                    'severity': 'medium',
                    'fix': 'Verificar que todos los activos estén correctamente registrados y valorados.',
                    'prompt_used': prompt
                })
        
        # Ratio gastos/ingresos
        if 'Gastos Totales' in pl_totals and 'Ingresos Totales' in pl_totals:
            expenses = pl_totals['Gastos Totales']
            revenue = pl_totals['Ingresos Totales']
            ratio = expenses / revenue if revenue != 0 else 0
            
            prompt = ANALYSIS_PROMPTS['expense_revenue_ratio'].format(
                expenses=expenses,
                revenue=revenue,
                ratio=ratio
            )
            
            if expenses > revenue:
                discrepancies.append({
                    'type': 'expense_ratio',
                    'description': f"Los gastos (${expenses}) son mayores que los ingresos (${revenue})",
                    'severity': 'high',
                    'fix': 'Revisar y validar todos los gastos registrados. Verificar si hay gastos duplicados o incorrectamente clasificados.',
                    'prompt_used': prompt
                })
        
        return discrepancies
    
    def _find_net_income(self, data: Dict) -> Optional[Decimal]:
        """Encuentra la utilidad neta en los datos."""
        totals = data.get('totals', {})
        for key in ['Utilidad Neta', 'Net Income', 'Resultado Neto']:
            if key in totals:
                return totals[key]
        return None 