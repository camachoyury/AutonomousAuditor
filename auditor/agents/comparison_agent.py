from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, List, Optional
from decimal import Decimal
from ..core.adk_prompts import (
    FINANCIAL_VALIDATION_PROMPT,
    RATIO_ANALYSIS_PROMPT,
    BALANCE_VALIDATION_PROMPT
)
from ..core.adk_parser import (
    parse_validation_response,
    parse_ratio_response,
    parse_balance_response
)

class ComparisonAgent(Agent):
    """Agente especializado en comparar documentos financieros usando ADK."""
    
    def __init__(self):
        super().__init__(
            name="comparison_agent",
            model="gemini-2.0-flash",
            description="Agente para comparar documentos financieros y detectar discrepancias",
            tools=[
                FunctionTool(self.validate_financial_documents),
                FunctionTool(self.analyze_ratios),
                FunctionTool(self.validate_balance_equation)
            ]
        )
    
    def validate_financial_documents(self, pl_data: Dict, balance_data: Dict) -> List[Dict]:
        """Valida la consistencia entre P&L y Balance usando ADK."""
        prompt = FINANCIAL_VALIDATION_PROMPT.format(
            pl_data=pl_data,
            balance_data=balance_data
        )
        
        response = self.generate(prompt)
        return parse_validation_response(response)
    
    def analyze_ratios(self, pl_data: Dict, balance_data: Dict) -> List[Dict]:
        """Analiza ratios financieros usando ADK."""
        # Calcular ratios
        revenue = pl_data.get('totals', {}).get('Ingresos Totales', Decimal('0'))
        expenses = pl_data.get('totals', {}).get('Gastos Totales', Decimal('0'))
        assets = balance_data.get('totals', {}).get('Total Activos', Decimal('0'))
        liabilities = balance_data.get('totals', {}).get('Total Pasivos', Decimal('0'))
        
        revenue_assets_ratio = revenue / assets if assets else Decimal('0')
        expense_revenue_ratio = expenses / revenue if revenue else Decimal('0')
        liability_assets_ratio = liabilities / assets if assets else Decimal('0')
        
        prompt = RATIO_ANALYSIS_PROMPT.format(
            revenue_assets_ratio=revenue_assets_ratio,
            expense_revenue_ratio=expense_revenue_ratio,
            liability_assets_ratio=liability_assets_ratio
        )
        
        response = self.generate(prompt)
        return parse_ratio_response(response)
    
    def validate_balance_equation(self, balance_data: Dict) -> List[Dict]:
        """Valida la ecuación contable usando ADK."""
        assets = balance_data.get('totals', {}).get('Total Activos', Decimal('0'))
        liabilities = balance_data.get('totals', {}).get('Total Pasivos', Decimal('0'))
        equity = balance_data.get('totals', {}).get('Total Capital Contable', Decimal('0'))
        
        difference = assets - (liabilities + equity)
        
        prompt = BALANCE_VALIDATION_PROMPT.format(
            total_assets=assets,
            total_liabilities=liabilities,
            total_equity=equity,
            difference=difference,
            tolerance=Decimal('0.01')
        )
        
        response = self.generate(prompt)
        return parse_balance_response(response) 