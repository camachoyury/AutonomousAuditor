"""Módulo que contiene todos los prompts utilizados por el sistema de auditoría financiera."""

MAIN_AGENT_PROMPT = """Soy un agente especializado en auditoría financiera con las siguientes responsabilidades:

1. Recuperación de Documentos:
   - Obtener P&L y Balance Sheet del repositorio GitHub
   - Verificar que los documentos correspondan al mismo período

2. Análisis de Consistencia:
   - Comparar números entre P&L y Balance Sheet
   - Verificar que la utilidad neta coincida con el cambio en ganancias retenidas
   - Validar que los totales sean consistentes

3. Detección de Anomalías:
   - Identificar ratios inusuales (ej: ingresos vs activos)
   - Detectar gastos excesivos
   - Verificar que el balance esté balanceado

4. Generación de Reportes:
   - Crear issues en GitHub con hallazgos
   - Clasificar discrepancias por severidad
   - Proponer correcciones específicas

Mi objetivo es asegurar la integridad y consistencia de los reportes financieros."""

COMPARISON_PROMPTS = {
    'period_match': """Verifica que los períodos en ambos documentos coincidan.
    P&L: {pl_period}
    Balance: {balance_period}""",
    
    'net_income': """Compara la utilidad neta entre documentos:
    P&L: ${pl_net_income}
    Balance: ${balance_net_income}
    Tolerancia: ${tolerance}""",
    
    'retained_earnings': """Verifica que las ganancias retenidas reflejen la utilidad del período:
    Ganancias Retenidas Actuales: ${current_retained}
    Utilidad del Período: ${net_income}
    Ganancias Retenidas Esperadas: ${expected_retained}"""
}

ANALYSIS_PROMPTS = {
    'revenue_assets_ratio': """Analiza la relación entre ingresos y activos:
    Ingresos Totales: ${revenue}
    Total Activos: ${assets}
    Ratio: ${ratio}
    Considerar como inusual si ratio > 2""",
    
    'expense_revenue_ratio': """Analiza la relación entre gastos e ingresos:
    Gastos Totales: ${expenses}
    Ingresos Totales: ${revenue}
    Ratio: ${ratio}
    Considerar como inusual si gastos > ingresos""",
    
    'balance_equation': """Verifica la ecuación contable:
    Activos: ${assets}
    Pasivos: ${liabilities}
    Capital: ${equity}
    Diferencia: ${difference}
    Tolerancia: ${tolerance}"""
}

REPORT_PROMPTS = {
    'issue_title': """Auditoría Financiera - {period} - {date}""",
    
    'issue_body': """# Reporte de Auditoría Financiera

## Resumen
- Período: {period}
- Fecha de Auditoría: {date}
- Total Discrepancias: {total_discrepancies}

## Hallazgos por Severidad
{severity_sections}

## Recomendaciones
{recommendations}

## Próximos Pasos
1. Revisar y validar todas las discrepancias
2. Implementar las correcciones propuestas
3. Ejecutar una nueva auditoría después de las correcciones
4. Considerar controles adicionales para prevenir futuras discrepancias"""
} 