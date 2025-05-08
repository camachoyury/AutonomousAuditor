from google.adk import Agent, Tool
from typing import Dict, List
from dataclasses import dataclass
from decimal import Decimal
import pandas as pd
from io import StringIO
import re

@dataclass
class FinancialLineItem:
    name: str
    amount: Decimal
    category: str
    period: str

class DocumentParserAgent(Agent):
    """Agente especializado en parsear documentos financieros."""
    
    def __init__(self):
        super().__init__()
    
    @Tool
    def parse_pl(self, content: str, format: str) -> Dict:
        """Parsea un documento de P&L.
        
        Args:
            content (str): Contenido del documento
            format (str): Formato del documento ('markdown' o 'csv')
        
        Returns:
            Dict: Datos estructurados del P&L
        """
        if format == 'markdown':
            return self._parse_pl_markdown(content)
        else:
            return self._parse_pl_csv(content)
    
    @Tool
    def parse_balance(self, content: str, format: str) -> Dict:
        """Parsea un documento de Balance General.
        
        Args:
            content (str): Contenido del documento
            format (str): Formato del documento ('markdown' o 'csv')
        
        Returns:
            Dict: Datos estructurados del Balance
        """
        if format == 'markdown':
            return self._parse_balance_markdown(content)
        else:
            return self._parse_balance_csv(content)
    
    def _parse_pl_markdown(self, content: str) -> Dict:
        """Parsea un P&L en formato Markdown."""
        lines = content.split('\n')
        data = {
            'period': None,
            'revenue': [],
            'expenses': [],
            'totals': {}
        }
        
        current_section = None
        period_match = re.search(r'Periodo:\s*([^\n]+)', content)
        if period_match:
            data['period'] = period_match.group(1).strip()

        for line in lines:
            line = line.strip()
            
            if line.startswith('##'):
                current_section = line.replace('#', '').strip().lower()
                continue
            
            if not line or line.startswith('|--') or line.startswith('| Concepto'):
                continue
            
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
                        elif current_section == 'totales':
                            data['totals'][name] = amount
                    except (ValueError, decimal.InvalidOperation):
                        continue

        return data
    
    def _parse_pl_csv(self, content: str) -> Dict:
        """Parsea un P&L en formato CSV."""
        try:
            df = pd.read_csv(StringIO(content))
            data = {
                'period': None,
                'revenue': [],
                'expenses': [],
                'totals': {}
            }
            
            for _, row in df.iterrows():
                try:
                    amount = Decimal(str(row['Amount']).replace('$', '').replace(',', ''))
                    item = FinancialLineItem(
                        name=row['Item'],
                        amount=amount,
                        category=row['Category'].lower(),
                        period=data['period']
                    )
                    
                    if row['Category'].lower() in ['ingresos', 'revenue', 'income']:
                        data['revenue'].append(item)
                    elif row['Category'].lower() in ['gastos', 'expenses', 'costs']:
                        data['expenses'].append(item)
                    elif row['Category'].lower() in ['total', 'totales']:
                        data['totals'][row['Item']] = amount
                except (ValueError, decimal.InvalidOperation, KeyError):
                    continue
            
            return data
        except Exception as e:
            raise ValueError(f"Error al parsear CSV: {str(e)}")
    
    def _parse_balance_markdown(self, content: str) -> Dict:
        """Parsea un Balance General en formato Markdown."""
        lines = content.split('\n')
        data = {
            'period': None,
            'activos': [],
            'pasivos': [],
            'capital_contable': [],
            'totals': {}
        }
        
        current_section = None
        period_match = re.search(r'Periodo:\s*([^\n]+)', content)
        if period_match:
            data['period'] = period_match.group(1).strip()

        for line in lines:
            line = line.strip()
            
            if line.startswith('##'):
                current_section = line.replace('#', '').strip().lower()
                continue
            
            if not line or line.startswith('|--') or line.startswith('| Concepto'):
                continue
            
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
                        elif current_section == 'capital contable':
                            data['capital_contable'].append(FinancialLineItem(
                                name=name,
                                amount=amount,
                                category='equity',
                                period=data['period']
                            ))
                        elif current_section == 'totales':
                            data['totals'][name] = amount
                    except (ValueError, decimal.InvalidOperation):
                        continue

        return data
    
    def _parse_balance_csv(self, content: str) -> Dict:
        """Parsea un Balance General en formato CSV."""
        try:
            df = pd.read_csv(StringIO(content))
            data = {
                'period': None,
                'activos': [],
                'pasivos': [],
                'capital_contable': [],
                'totals': {}
            }
            
            for _, row in df.iterrows():
                try:
                    amount = Decimal(str(row['Amount']).replace('$', '').replace(',', ''))
                    item = FinancialLineItem(
                        name=row['Item'],
                        amount=amount,
                        category=row['Category'].lower(),
                        period=data['period']
                    )
                    
                    if row['Category'].lower() in ['activos', 'assets']:
                        data['activos'].append(item)
                    elif row['Category'].lower() in ['pasivos', 'liabilities']:
                        data['pasivos'].append(item)
                    elif row['Category'].lower() in ['capital', 'equity']:
                        data['capital_contable'].append(item)
                    elif row['Category'].lower() in ['total', 'totales']:
                        data['totals'][row['Item']] = amount
                except (ValueError, decimal.InvalidOperation, KeyError):
                    continue
            
            return data
        except Exception as e:
            raise ValueError(f"Error al parsear CSV: {str(e)}") 