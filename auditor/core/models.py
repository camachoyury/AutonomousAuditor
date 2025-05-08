from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

@dataclass
class FinancialLineItem:
    """Representa un ítem financiero individual."""
    name: str
    amount: Decimal
    category: str
    period: str

@dataclass
class FinancialDocument:
    """Representa un documento financiero (P&L o Balance)."""
    content: str
    doc_type: str  # 'pl' o 'balance'
    file_format: str  # 'markdown' o 'csv'
    parsed_data: Optional[Dict] = None

@dataclass
class AuditResult:
    """Resultado de una auditoría financiera."""
    status: str
    discrepancies: List[Dict]
    issue_url: Optional[str] = None
    error_message: Optional[str] = None 