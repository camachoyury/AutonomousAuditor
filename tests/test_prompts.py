import os
import sys
from pathlib import Path
from decimal import Decimal
from auditor.core.prompts import (
    MAIN_AGENT_PROMPT,
    COMPARISON_PROMPTS,
    ANALYSIS_PROMPTS,
    REPORT_PROMPTS
)
from auditor.agent import AuditorAgent
from auditor.document_parser import FinancialDocument

def test_prompts():
    """Prueba los prompts del sistema."""
    print("\nProbando prompts del sistema...")
    
    # Imprimir prompt principal
    print("\nPrompt Principal:")
    print(MAIN_AGENT_PROMPT)
    
    # Cargar documentos de prueba
    test_dir = Path(__file__).parent / "test_data"
    pl_doc = FinancialDocument(test_dir / "pl.md")
    balance_doc = FinancialDocument(test_dir / "balance.md")
    
    # Probar prompts de comparación
    print("\nProbando prompts de comparación:")
    print("\nComparación de períodos:")
    print(COMPARISON_PROMPTS["period_match"])
    
    print("\nComparación de utilidad neta:")
    print(COMPARISON_PROMPTS["net_income"])
    
    print("\nComparación de utilidades retenidas:")
    print(COMPARISON_PROMPTS["retained_earnings"])
    
    # Probar prompts de análisis
    print("\nProbando prompts de análisis:")
    print("\nAnálisis de ratio ingresos/activos:")
    print(ANALYSIS_PROMPTS["revenue_assets_ratio"])
    
    print("\nAnálisis de ratio gastos/ingresos:")
    print(ANALYSIS_PROMPTS["expense_revenue_ratio"])
    
    print("\nAnálisis de ecuación contable:")
    print(ANALYSIS_PROMPTS["balance_equation"])
    
    # Probar prompts de reporte
    print("\nProbando prompts de reporte:")
    print("\nTítulo del issue:")
    print(REPORT_PROMPTS["issue_title"])
    
    print("\nCuerpo del issue:")
    print(REPORT_PROMPTS["issue_body"])
    
    # Probar agente principal
    print("\nProbando agente principal...")
    auditor = AuditorAgent()
    
    # Simular comparación de documentos
    pl_data = pl_doc.parse()
    balance_data = balance_doc.parse()
    
    discrepancies = auditor.analyze_documents({
        'pl': pl_doc,
        'balance': balance_doc
    })
    
    print(f"\nDiscrepancias encontradas: {len(discrepancies)}")
    for disc in discrepancies:
        print(f"\nTipo: {disc['type']}")
        print(f"Severidad: {disc['severity']}")
        print(f"Descripción: {disc['description']}")
        print(f"Recomendación: {disc.get('recommendation', disc.get('fix', 'No hay recomendación específica.'))}")

if __name__ == "__main__":
    test_prompts() 