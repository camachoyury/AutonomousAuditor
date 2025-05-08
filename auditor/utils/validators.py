from decimal import Decimal
from typing import Dict, Any

from ..core.exceptions import ValidationError
from ..core.constants import MIN_AMOUNT, MAX_AMOUNT

def validate_amount(amount: Decimal) -> bool:
    """Valida que un monto esté dentro de los rangos permitidos."""
    return MIN_AMOUNT <= amount <= MAX_AMOUNT

def validate_period(period: str) -> bool:
    """Valida que el período tenga un formato válido."""
    if not period:
        return False
    # Aquí se pueden agregar más validaciones específicas del formato del período
    return True

def validate_document_data(data: Dict[str, Any]) -> bool:
    """Valida la estructura y contenido de los datos del documento."""
    required_keys = ['period', 'totals']
    if not all(key in data for key in required_keys):
        return False
    
    # Validar montos en totales
    for amount in data['totals'].values():
        if not validate_amount(amount):
            return False
    
    return True

def validate_repo_url(url: str) -> bool:
    """Valida que la URL del repositorio tenga un formato válido."""
    if not url:
        return False
    if not url.startswith('https://github.com/'):
        return False
    parts = url.split('/')
    if len(parts) < 5:
        return False
    return True 