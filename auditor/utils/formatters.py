from decimal import Decimal
from typing import Dict, List
from datetime import datetime

def format_amount(amount: Decimal) -> str:
    """Formatea un monto con el símbolo de moneda y separadores de miles."""
    return f"${amount:,.2f}"

def format_period(period: str) -> str:
    """Formatea un período para su visualización."""
    return period.strip()

def format_discrepancy(discrepancy: Dict) -> str:
    """Formatea una discrepancia para su visualización."""
    return f"""
    Tipo: {discrepancy['type']}
    Descripción: {discrepancy['description']}
    Severidad: {discrepancy['severity']}
    Corrección propuesta: {discrepancy.get('fix', 'No hay propuesta específica.')}
    """

def format_audit_summary(discrepancies: List[Dict]) -> str:
    """Formatea un resumen de la auditoría."""
    high_severity = [d for d in discrepancies if d['severity'] == 'high']
    medium_severity = [d for d in discrepancies if d['severity'] == 'medium']
    low_severity = [d for d in discrepancies if d['severity'] == 'low']
    
    return f"""
    Resumen de Auditoría:
    - Total de discrepancias: {len(discrepancies)}
    - Severidad Alta: {len(high_severity)}
    - Severidad Media: {len(medium_severity)}
    - Severidad Baja: {len(low_severity)}
    """

def format_timestamp() -> str:
    """Formatea la fecha y hora actual."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S') 