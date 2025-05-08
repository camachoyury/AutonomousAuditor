from typing import Dict, List
import pandas as pd
from io import StringIO
import re
from decimal import Decimal, InvalidOperation

from ..core.models import FinancialLineItem, FinancialDocument
from ..core.exceptions import DocumentParseError
from ..core.constants import (
    FORMAT_MARKDOWN, FORMAT_CSV,
    CATEGORY_REVENUE, CATEGORY_EXPENSE,
    CATEGORY_ASSET, CATEGORY_LIABILITY, CATEGORY_EQUITY,
    MIN_AMOUNT, MAX_AMOUNT
)

class DocumentService:
    """Servicio para parsear documentos financieros."""

    def parse_document(self, document: FinancialDocument) -> Dict:
        """Parsea un documento financiero."""
        if document.file_format == FORMAT_MARKDOWN:
            if document.doc_type == 'pl':
                return self._parse_pl_markdown(document.content)
            else:
                return self._parse_balance_markdown(document.content)
        else:
            if document.doc_type == 'pl':
                return self._parse_pl_csv(document.content)
            else:
                return self._parse_balance_csv(document.content)

    def _parse_pl_markdown(self, content: str) -> Dict:
        """Parsea un P&L en formato Markdown."""
        try:
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
                            if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
                                continue
                            
                            if current_section == 'ingresos':
                                data['revenue'].append(FinancialLineItem(
                                    name=name,
                                    amount=amount,
                                    category=CATEGORY_REVENUE,
                                    period=data['period']
                                ))
                            elif current_section == 'gastos':
                                data['expenses'].append(FinancialLineItem(
                                    name=name,
                                    amount=amount,
                                    category=CATEGORY_EXPENSE,
                                    period=data['period']
                                ))
                            elif current_section == 'totales':
                                data['totals'][name] = amount
                        except (ValueError, InvalidOperation):
                            continue
            
            if not data['period']:
                raise DocumentParseError("No se encontró el período en el documento")
            
            return data
            
        except Exception as e:
            raise DocumentParseError(f"Error al parsear P&L en Markdown: {str(e)}")

    def _parse_balance_markdown(self, content: str) -> Dict:
        """Parsea un Balance General en formato Markdown."""
        try:
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
                            if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
                                continue
                            
                            if current_section == 'activos':
                                data['activos'].append(FinancialLineItem(
                                    name=name,
                                    amount=amount,
                                    category=CATEGORY_ASSET,
                                    period=data['period']
                                ))
                            elif current_section == 'pasivos':
                                data['pasivos'].append(FinancialLineItem(
                                    name=name,
                                    amount=amount,
                                    category=CATEGORY_LIABILITY,
                                    period=data['period']
                                ))
                            elif current_section == 'capital contable':
                                data['capital_contable'].append(FinancialLineItem(
                                    name=name,
                                    amount=amount,
                                    category=CATEGORY_EQUITY,
                                    period=data['period']
                                ))
                            elif current_section == 'totales':
                                data['totals'][name] = amount
                        except (ValueError, InvalidOperation):
                            continue
            
            if not data['period']:
                raise DocumentParseError("No se encontró el período en el documento")
            
            return data
            
        except Exception as e:
            raise DocumentParseError(f"Error al parsear Balance en Markdown: {str(e)}")

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
            
            # Buscar período
            period_col = df.columns[df.columns.str.contains('periodo', case=False)][0]
            data['period'] = df[period_col].iloc[0]
            
            for _, row in df.iterrows():
                try:
                    amount = Decimal(str(row['Amount']).replace('$', '').replace(',', ''))
                    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
                        continue
                    
                    if row['Category'].lower() == 'revenue':
                        data['revenue'].append(FinancialLineItem(
                            name=row['Item'],
                            amount=amount,
                            category=CATEGORY_REVENUE,
                            period=data['period']
                        ))
                    elif row['Category'].lower() == 'expense':
                        data['expenses'].append(FinancialLineItem(
                            name=row['Item'],
                            amount=amount,
                            category=CATEGORY_EXPENSE,
                            period=data['period']
                        ))
                    elif row['Category'].lower() in ['total', 'totales']:
                        data['totals'][row['Item']] = amount
                except (ValueError, InvalidOperation, KeyError):
                    continue
            
            return data
            
        except Exception as e:
            raise DocumentParseError(f"Error al parsear P&L en CSV: {str(e)}")

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
            
            # Buscar período
            period_col = df.columns[df.columns.str.contains('periodo', case=False)][0]
            data['period'] = df[period_col].iloc[0]
            
            for _, row in df.iterrows():
                try:
                    amount = Decimal(str(row['Amount']).replace('$', '').replace(',', ''))
                    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
                        continue
                    
                    if row['Category'].lower() == 'asset':
                        data['activos'].append(FinancialLineItem(
                            name=row['Item'],
                            amount=amount,
                            category=CATEGORY_ASSET,
                            period=data['period']
                        ))
                    elif row['Category'].lower() == 'liability':
                        data['pasivos'].append(FinancialLineItem(
                            name=row['Item'],
                            amount=amount,
                            category=CATEGORY_LIABILITY,
                            period=data['period']
                        ))
                    elif row['Category'].lower() == 'equity':
                        data['capital_contable'].append(FinancialLineItem(
                            name=row['Item'],
                            amount=amount,
                            category=CATEGORY_EQUITY,
                            period=data['period']
                        ))
                    elif row['Category'].lower() in ['total', 'totales']:
                        data['totals'][row['Item']] = amount
                except (ValueError, InvalidOperation, KeyError):
                    continue
            
            return data
            
        except Exception as e:
            raise DocumentParseError(f"Error al parsear Balance en CSV: {str(e)}") 