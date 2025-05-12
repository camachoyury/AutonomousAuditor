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
from auditor.agent import FinancialDocument, compare_documents

def test_prompts():
    """Prueba los prompts del sistema con datos de ejemplo."""
    print("\n=== Probando Prompts del Sistema ===\n")
    
    # 1. Probar prompt principal
    print("1. Prompt Principal:")
    print(MAIN_AGENT_PROMPT)
    print("\n" + "="*50 + "\n")
    
    # 2. Cargar documentos de prueba
    test_dir = Path(__file__).parent / "test_data"
    with open(test_dir / "pl.md", "r") as f:
        pl_content = f.read()
    with open(test_dir / "balance.md", "r") as f:
        balance_content = f.read()
    
    pl_doc = FinancialDocument(pl_content, "pl")
    balance_doc = FinancialDocument(balance_content, "balance")
    
    # 3. Probar prompts de comparación
    print("2. Prompts de Comparación:")
    
    # Periodo
    period_prompt = COMPARISON_PROMPTS['period_match'].format(
        pl_period="Q1 2024",
        balance_period="Q1 2024"
    )
    print("\nPrompt de Comparación de Períodos:")
    print(period_prompt)
    
    # Utilidad Neta
    net_income_prompt = COMPARISON_PROMPTS['net_income'].format(
        pl_net_income=Decimal("550000"),
        balance_net_income=Decimal("550000"),
        tolerance=Decimal("0.01")
    )
    print("\nPrompt de Comparación de Utilidad Neta:")
    print(net_income_prompt)
    
    # Ganancias Retenidas
    retained_earnings_prompt = COMPARISON_PROMPTS['retained_earnings'].format(
        current_retained=Decimal("450000"),
        net_income=Decimal("550000"),
        expected_retained=Decimal("1000000")
    )
    print("\nPrompt de Comparación de Ganancias Retenidas:")
    print(retained_earnings_prompt)
    print("\n" + "="*50 + "\n")
    
    # 4. Probar prompts de análisis
    print("3. Prompts de Análisis:")
    
    # Ratio Ingresos/Activos
    revenue_assets_prompt = ANALYSIS_PROMPTS['revenue_assets_ratio'].format(
        revenue=Decimal("1600000"),
        assets=Decimal("1900000"),
        ratio=Decimal("0.84")
    )
    print("\nPrompt de Análisis de Ratio Ingresos/Activos:")
    print(revenue_assets_prompt)
    
    # Ratio Gastos/Ingresos
    expense_revenue_prompt = ANALYSIS_PROMPTS['expense_revenue_ratio'].format(
        expenses=Decimal("1050000"),
        revenue=Decimal("1600000"),
        ratio=Decimal("0.66")
    )
    print("\nPrompt de Análisis de Ratio Gastos/Ingresos:")
    print(expense_revenue_prompt)
    
    # Ecuación Contable
    balance_equation_prompt = ANALYSIS_PROMPTS['balance_equation'].format(
        assets=Decimal("1900000"),
        liabilities=Decimal("850000"),
        equity=Decimal("1050000"),
        difference=Decimal("0"),
        tolerance=Decimal("0.01")
    )
    print("\nPrompt de Análisis de Ecuación Contable:")
    print(balance_equation_prompt)
    print("\n" + "="*50 + "\n")
    
    # 5. Probar prompts de reporte
    print("4. Prompts de Reporte:")
    
    # Título del Issue
    issue_title = REPORT_PROMPTS['issue_title'].format(
        period="Q1 2024",
        date="2024-03-20"
    )
    print("\nTítulo del Issue:")
    print(issue_title)
    
    # Cuerpo del Issue
    severity_sections = """
### 🔴 Discrepancias de Alta Severidad
- La utilidad neta no coincide entre documentos
  - **Propuesta de Corrección**: Ajustar la utilidad neta en el Balance

### 🟡 Discrepancias de Severidad Media
- Los ingresos son inusualmente altos en comparación con los activos
  - **Propuesta de Corrección**: Verificar la valoración de activos
"""
    
    recommendations = """
- Priorizar la corrección de las discrepancias de alta severidad
- Revisar y corregir las discrepancias de severidad media
"""
    
    issue_body = REPORT_PROMPTS['issue_body'].format(
        period="Q1 2024",
        date="2024-03-20 15:30:00",
        total_discrepancies=2,
        severity_sections=severity_sections,
        recommendations=recommendations
    )
    print("\nCuerpo del Issue:")
    print(issue_body)
    print("\n" + "="*50 + "\n")
    
    # 6. Probar comparación real de documentos
    print("5. Comparación Real de Documentos:")
    discrepancies = compare_documents(pl_doc, balance_doc)
    print(f"\nDiscrepancias encontradas: {len(discrepancies)}")
    for d in discrepancies:
        print(f"\nTipo: {d['type']}")
        print(f"Descripción: {d['description']}")
        print(f"Severidad: {d['severity']}")
        if 'fix' in d:
            print(f"Corrección: {d['fix']}")
        if 'prompt_used' in d:
            print(f"Prompt usado: {d['prompt_used']}")

if __name__ == "__main__":
    test_prompts() 