"""Módulo para parsear documentos financieros."""

import re
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class FinancialLineItem:
    """Representa una línea de un documento financiero."""
    name: str
    amount: Decimal
    category: str
    period: Optional[str] = None

class FinancialDocument:
    """Clase para parsear y manejar documentos financieros."""
    
    def __init__(self, file_path: Path) -> None:
        """Inicializa un documento financiero.
        
        Args:
            file_path: Ruta al archivo del documento.
        """
        self.file_path = file_path
        self.content = file_path.read_text()
        self.doc_type = 'pl' if 'pl' in file_path.name.lower() else 'balance'
        self.parsed_data: Optional[Dict[str, Any]] = None
    
    def parse(self) -> Dict[str, Any]:
        """Parsea el documento financiero y extrae los datos relevantes."""
        if self.doc_type == 'pl':
            return self._parse_pl()
        else:
            return self._parse_balance()
    
    def _parse_pl(self) -> Dict[str, Any]:
        """Parsea un documento de P&L y extrae los datos relevantes."""
        data = {
            'period': None,
            'revenue': [],
            'expenses': [],
            'totals': {}
        }
        
        # Extraer período
        period_match = re.search(r'Período:\s*([^\n]+)', self.content)
        if period_match:
            data['period'] = period_match.group(1).strip()
        
        # Procesar líneas
        current_section = None
        for line in self.content.split('\n'):
            line = line.strip()
            
            # Detectar secciones
            if line.startswith('###'):
                current_section = line.replace('#', '').strip().lower()
                continue
            
            # Ignorar líneas vacías o encabezados de tabla
            if not line or line.startswith('|--') or line.startswith('| Concepto'):
                continue
            
            # Procesar líneas de datos
            if line.startswith('|'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) >= 2:
                    name = cells[0]
                    try:
                        amount = Decimal(cells[1].replace('$', '').replace(',', '').strip())
                        
                        if current_section == 'ingresos':
                            data['revenue'].append(FinancialLineItem(
                                name=name,
                                amount=amount,
                                category='revenue',
                                period=data['period']
                            ))
                        elif current_section == 'gastos':
                            data['expenses'].append(FinancialLineItem(
                                name=name,
                                amount=amount,
                                category='expense',
                                period=data['period']
                            ))
                        elif current_section == 'resultado':
                            data['totals'][name] = amount
                    except (ValueError, decimal.InvalidOperation):
                        continue
        
        return data
    
    def _parse_balance(self) -> Dict[str, Any]:
        """Parsea un Balance General y extrae los datos relevantes."""
        data = {
            'period': None,
            'activos': [],
            'pasivos': [],
            'capital': [],
            'totals': {}
        }
        
        # Extraer período
        period_match = re.search(r'Período:\s*([^\n]+)', self.content)
        if period_match:
            data['period'] = period_match.group(1).strip()
        
        # Procesar líneas
        current_section = None
        for line in self.content.split('\n'):
            line = line.strip()
            
            # Detectar secciones
            if line.startswith('###'):
                current_section = line.replace('#', '').strip().lower()
                continue
            
            # Ignorar líneas vacías o encabezados de tabla
            if not line or line.startswith('|--') or line.startswith('| Concepto'):
                continue
            
            # Procesar líneas de datos
            if line.startswith('|'):
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) >= 2:
                    name = cells[0]
                    try:
                        amount = Decimal(cells[1].replace('$', '').replace(',', '').strip())
                        
                        if current_section == 'activos':
                            data['activos'].append(FinancialLineItem(
                                name=name,
                                amount=amount,
                                category='asset',
                                period=data['period']
                            ))
                        elif current_section == 'pasivos':
                            data['pasivos'].append(FinancialLineItem(
                                name=name,
                                amount=amount,
                                category='liability',
                                period=data['period']
                            ))
                        elif current_section == 'capital':
                            data['capital'].append(FinancialLineItem(
                                name=name,
                                amount=amount,
                                category='equity',
                                period=data['period']
                            ))
                        elif name.startswith('Total'):
                            data['totals'][name] = amount
                    except (ValueError, decimal.InvalidOperation):
                        continue
        
        return data 