"""Módulo para parsear respuestas de ADK en validaciones financieras."""

from typing import Dict, List
import json
from decimal import Decimal

def parse_validation_response(response: str) -> List[Dict]:
    """Parsea la respuesta de ADK para validación general de documentos."""
    try:
        # Intentar parsear como JSON
        data = json.loads(response)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    
    # Si no es JSON, intentar extraer información estructurada
    discrepancies = []
    current_discrepancy = {}
    
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            if current_discrepancy:
                discrepancies.append(current_discrepancy)
                current_discrepancy = {}
            continue
            
        if line.startswith('Tipo:'):
            current_discrepancy['type'] = line.replace('Tipo:', '').strip()
        elif line.startswith('Descripción:'):
            current_discrepancy['description'] = line.replace('Descripción:', '').strip()
        elif line.startswith('Severidad:'):
            current_discrepancy['severity'] = line.replace('Severidad:', '').strip()
        elif line.startswith('Solución:'):
            current_discrepancy['fix'] = line.replace('Solución:', '').strip()
    
    if current_discrepancy:
        discrepancies.append(current_discrepancy)
    
    return discrepancies

def parse_ratio_response(response: str) -> List[Dict]:
    """Parsea la respuesta de ADK para análisis de ratios."""
    try:
        # Intentar parsear como JSON
        data = json.loads(response)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    
    # Si no es JSON, intentar extraer información estructurada
    discrepancies = []
    current_ratio = {}
    
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            if current_ratio:
                discrepancies.append(current_ratio)
                current_ratio = {}
            continue
            
        if line.startswith('Ratio:'):
            current_ratio['type'] = f"ratio_{line.replace('Ratio:', '').strip().lower()}"
        elif line.startswith('Valor:'):
            try:
                current_ratio['value'] = Decimal(line.replace('Valor:', '').strip())
            except:
                pass
        elif line.startswith('Rango Normal:'):
            current_ratio['normal_range'] = line.replace('Rango Normal:', '').strip()
        elif line.startswith('Análisis:'):
            current_ratio['description'] = line.replace('Análisis:', '').strip()
        elif line.startswith('Recomendación:'):
            current_ratio['fix'] = line.replace('Recomendación:', '').strip()
    
    if current_ratio:
        discrepancies.append(current_ratio)
    
    return discrepancies

def parse_balance_response(response: str) -> List[Dict]:
    """Parsea la respuesta de ADK para validación de balance."""
    try:
        # Intentar parsear como JSON
        data = json.loads(response)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    
    # Si no es JSON, intentar extraer información estructurada
    discrepancies = []
    current_issue = {}
    
    for line in response.split('\n'):
        line = line.strip()
        if not line:
            if current_issue:
                discrepancies.append(current_issue)
                current_issue = {}
            continue
            
        if line.startswith('Tipo:'):
            current_issue['type'] = line.replace('Tipo:', '').strip()
        elif line.startswith('Diferencia:'):
            try:
                current_issue['difference'] = Decimal(line.replace('Diferencia:', '').strip())
            except:
                pass
        elif line.startswith('Análisis:'):
            current_issue['description'] = line.replace('Análisis:', '').strip()
        elif line.startswith('Causas Posibles:'):
            current_issue['possible_causes'] = line.replace('Causas Posibles:', '').strip()
        elif line.startswith('Sugerencias:'):
            current_issue['fix'] = line.replace('Sugerencias:', '').strip()
    
    if current_issue:
        discrepancies.append(current_issue)
    
    return discrepancies 