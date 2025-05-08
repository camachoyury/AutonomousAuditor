from google.adk import Agent, Tool
from typing import Dict, List
from decimal import Decimal

class ComparisonAgent(Agent):
    """Agente especializado en comparar documentos financieros."""
    
    def __init__(self):
        super().__init__()
    
    @Tool
    def compare_documents(self, pl_data: Dict, balance_data: Dict) -> List[Dict]:
        """Compara los documentos financieros y detecta inconsistencias.
        
        Args:
            pl_data (Dict): Datos del P&L
            balance_data (Dict): Datos del Balance General
        
        Returns:
            List[Dict]: Lista de discrepancias encontradas
        """
        discrepancies = []
        
        # Verificar que los períodos coincidan
        if pl_data.get('period') != balance_data.get('period'):
            discrepancies.append({
                'type': 'period_mismatch',
                'description': f"Los períodos no coinciden: P&L ({pl_data.get('period')}) vs Balance ({balance_data.get('period')})",
                'severity': 'high'
            })
        
        # Verificar que la utilidad neta coincida con la utilidad del período en el balance
        pl_net_income = None
        for item in pl_data.get('totals', {}).items():
            if 'utilidad' in item[0].lower() or 'net' in item[0].lower():
                pl_net_income = item[1]
                break
        
        balance_net_income = None
        for item in balance_data.get('capital_contable', []):
            if 'utilidad' in item.name.lower() or 'net' in item.name.lower():
                balance_net_income = item.amount
                break
        
        if pl_net_income is not None and balance_net_income is not None:
            if abs(pl_net_income - balance_net_income) > Decimal('0.01'):
                discrepancies.append({
                    'type': 'income_mismatch',
                    'description': f"La utilidad neta no coincide: P&L (${pl_net_income}) vs Balance (${balance_net_income})",
                    'severity': 'high'
                })
        
        # Verificar que los totales sean consistentes
        pl_totals = pl_data.get('totals', {})
        balance_totals = balance_data.get('totals', {})
        
        # Verificar que los ingresos totales sean razonables en comparación con los activos
        if 'Ingresos Totales' in pl_totals and 'Total Activos' in balance_totals:
            revenue = pl_totals['Ingresos Totales']
            assets = balance_totals['Total Activos']
            if revenue > assets * Decimal('2'):  # Si los ingresos son más del doble de los activos
                discrepancies.append({
                    'type': 'unusual_ratio',
                    'description': f"Los ingresos (${revenue}) son inusualmente altos en comparación con los activos (${assets})",
                    'severity': 'medium'
                })
        
        # Verificar que los gastos totales sean razonables en comparación con los ingresos
        if 'Gastos Totales' in pl_totals and 'Ingresos Totales' in pl_totals:
            expenses = pl_totals['Gastos Totales']
            revenue = pl_totals['Ingresos Totales']
            if expenses > revenue:  # Si los gastos son mayores que los ingresos
                discrepancies.append({
                    'type': 'expense_ratio',
                    'description': f"Los gastos (${expenses}) son mayores que los ingresos (${revenue})",
                    'severity': 'high'
                })
        
        # Verificar que el balance esté balanceado
        if 'Total Activos' in balance_totals and 'Total Pasivos' in balance_totals and 'Total Capital Contable' in balance_totals:
            assets = balance_totals['Total Activos']
            liabilities = balance_totals['Total Pasivos']
            equity = balance_totals['Total Capital Contable']
            
            if abs(assets - (liabilities + equity)) > Decimal('0.01'):
                discrepancies.append({
                    'type': 'unbalanced',
                    'description': f"El balance no está balanceado: Activos (${assets}) ≠ Pasivos (${liabilities}) + Capital (${equity})",
                    'severity': 'high'
                })
        
        return discrepancies 