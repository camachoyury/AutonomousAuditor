"""Prompts específicos para ADK en la validación financiera."""

FINANCIAL_VALIDATION_PROMPT = """Eres un experto en auditoría financiera. Tu tarea es validar la consistencia y precisión de los estados financieros.

Reglas de Validación:
1. Los períodos deben coincidir entre P&L y Balance
2. La utilidad neta del P&L debe coincidir con el cambio en ganancias retenidas
3. Los totales deben ser consistentes
4. Los ratios deben estar dentro de rangos razonables
5. El balance debe estar balanceado (A = P + C)

Documentos a validar:
P&L:
{pl_data}

Balance:
{balance_data}

Por favor, analiza estos documentos y reporta cualquier discrepancia o anomalía encontrada."""

RATIO_ANALYSIS_PROMPT = """Analiza los siguientes ratios financieros y determina si están dentro de rangos razonables:

1. Ingresos/Activos: {revenue_assets_ratio}
   - Rango normal: 0.5 - 2.0
   - Valores > 2.0 pueden indicar sobreestimación de ingresos
   - Valores < 0.5 pueden indicar activos subutilizados

2. Gastos/Ingresos: {expense_revenue_ratio}
   - Rango normal: 0.6 - 0.9
   - Valores > 0.9 pueden indicar ineficiencia operativa
   - Valores < 0.6 pueden indicar gastos no registrados

3. Pasivos/Activos: {liability_assets_ratio}
   - Rango normal: 0.4 - 0.7
   - Valores > 0.7 pueden indicar alto apalancamiento
   - Valores < 0.4 pueden indicar subutilización de deuda

Por favor, identifica cualquier ratio que esté fuera de estos rangos y explica las posibles implicaciones."""

BALANCE_VALIDATION_PROMPT = """Valida la ecuación contable básica: Activos = Pasivos + Capital Contable

Datos actuales:
- Total Activos: ${total_assets}
- Total Pasivos: ${total_liabilities}
- Total Capital Contable: ${total_equity}
- Diferencia: ${difference}

La diferencia debe ser cercana a cero (tolerancia: ${tolerance}).
Si hay una diferencia significativa, identifica posibles causas y sugerencias de corrección.""" 