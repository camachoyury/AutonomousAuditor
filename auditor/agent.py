import sys
import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd
import markdown
import re
from dataclasses import dataclass
from decimal import Decimal
from io import StringIO
import os
from github import Github
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from auditor.core.prompts import MAIN_AGENT_PROMPT, COMPARISON_PROMPTS, ANALYSIS_PROMPTS, REPORT_PROMPTS
from .agents.comparison_agent import ComparisonAgent
from .agents.issue_manager import IssueManagerAgent

# Cargar variables de entorno
load_dotenv()

@dataclass
class FinancialLineItem:
    name: str
    amount: Decimal
    category: str
    period: Optional[str]

class FinancialDocument:
    def __init__(self, content: str, doc_type: str) -> None:
        self.content: str = content
        self.doc_type: str = doc_type  # 'pl' o 'balance'
        self.parsed_data: Optional[Dict[str, Any]] = None
        self.file_format: str = self._detect_format()

    def _detect_format(self) -> str:
        """Detecta si el documento es Markdown o CSV."""
        if self.content.strip().startswith('|') or self.content.strip().startswith('#'):
            return 'markdown'
        return 'csv'

    def parse(self) -> Dict[str, Any]:
        """Parsea el documento financiero y extrae los datos relevantes."""
        if self.doc_type == 'pl':
            return self._parse_pl()
        else:
            return self._parse_balance()

    def _parse_pl(self) -> Dict[str, Any]:
        """Parsea un documento de P&L y extrae los datos relevantes."""
        try:
            if self.file_format == 'markdown':
                return self._parse_pl_markdown()
            else:
                return self._parse_pl_csv()
        except Exception as e:
            raise ValueError(f"Error al parsear el P&L: {str(e)}")

    def _parse_pl_markdown(self) -> Dict[str, Any]:
        """Parsea un P&L en formato Markdown."""
        lines: List[str] = self.content.split('\n')
        data: Dict[str, Any] = {
            'period': None,
            'revenue': [],
            'expenses': [],
            'totals': {}
        }
        
        current_section: Optional[str] = None
        period_match: Optional[re.Match] = re.search(r'Periodo:\s*([^\n]+)', self.content)
        if period_match:
            data['period'] = period_match.group(1).strip()

        for line in lines:
            line = line.strip()
            
            # Detectar secciones
            if line.startswith('##'):
                current_section = line.replace('#', '').strip().lower()
                continue
            
            # Ignorar líneas vacías o encabezados de tabla
            if not line or line.startswith('|--') or line.startswith('| Concepto'):
                continue
            
            # Procesar líneas de datos
            if line.startswith('|'):
                cells: List[str] = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) >= 2:
                    name: str = cells[0]
                    try:
                        amount: Decimal = Decimal(cells[1].replace('$', '').replace(',', '').strip())
                        
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

    def _parse_pl_csv(self) -> Dict[str, Any]:
        """Parsea un P&L en formato CSV."""
        try:
            df: pd.DataFrame = pd.read_csv(StringIO(self.content))
            data: Dict[str, Any] = {
                'period': None,
                'revenue': [],
                'expenses': [],
                'totals': {}
            }
            
            # Asumimos que el CSV tiene columnas: Category, Item, Amount
            for _, row in df.iterrows():
                try:
                    amount: Decimal = Decimal(str(row['Amount']).replace('$', '').replace(',', ''))
                    item: FinancialLineItem = FinancialLineItem(
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

    def _parse_balance(self) -> Dict[str, Any]:
        """Parsea un Balance General y extrae los datos relevantes."""
        try:
            if self.file_format == 'markdown':
                return self._parse_balance_markdown()
            else:
                return self._parse_balance_csv()
        except Exception as e:
            raise ValueError(f"Error al parsear el Balance: {str(e)}")

    def _parse_balance_markdown(self) -> Dict[str, Any]:
        """Parsea un Balance General en formato Markdown."""
        lines: List[str] = self.content.split('\n')
        data: Dict[str, Any] = {
            'period': None,
            'activos': [],
            'pasivos': [],
            'capital_contable': [],
            'totals': {}
        }
        
        current_section: Optional[str] = None
        period_match: Optional[re.Match] = re.search(r'Periodo:\s*([^\n]+)', self.content)
        if period_match:
            data['period'] = period_match.group(1).strip()

        for line in lines:
            line = line.strip()
            
            # Detectar secciones
            if line.startswith('##'):
                current_section = line.replace('#', '').strip().lower()
                continue
            
            # Ignorar líneas vacías o encabezados de tabla
            if not line or line.startswith('|--') or line.startswith('| Concepto'):
                continue
            
            # Procesar líneas de datos
            if line.startswith('|'):
                cells: List[str] = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) >= 2:
                    name: str = cells[0]
                    try:
                        amount: Decimal = Decimal(cells[1].replace('$', '').replace(',', '').strip())
                        
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

    def _parse_balance_csv(self) -> Dict[str, Any]:
        """Parsea un Balance General en formato CSV."""
        try:
            df: pd.DataFrame = pd.read_csv(StringIO(self.content))
            data: Dict[str, Any] = {
                'period': None,
                'activos': [],
                'pasivos': [],
                'capital_contable': [],
                'totals': {}
            }
            
            # Asumimos que el CSV tiene columnas: Category, Item, Amount
            for _, row in df.iterrows():
                try:
                    amount: Decimal = Decimal(str(row['Amount']).replace('$', '').replace(',', ''))
                    item: FinancialLineItem = FinancialLineItem(
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

def compare_documents(pl_content: str, balance_content: str) -> List[Dict[str, Any]]:
    """Compara los documentos financieros y detecta inconsistencias.

    Args:
        pl_content (str): Contenido del documento P&L
        balance_content (str): Contenido del documento Balance

    Returns:
        List[Dict]: Lista de discrepancias encontradas con propuestas de corrección
    """
    # Crear instancias de FinancialDocument
    pl_doc = FinancialDocument(pl_content, 'pl')
    balance_doc = FinancialDocument(balance_content, 'balance')
    
    # Parsear ambos documentos
    pl_data = pl_doc.parse()
    balance_data = balance_doc.parse()
    
    discrepancies = []
    
    # Verificar que los períodos coincidan
    if pl_data.get('period') != balance_data.get('period'):
        discrepancies.append({
            'type': 'period_mismatch',
            'description': f"Los períodos no coinciden: P&L ({pl_data.get('period')}) vs Balance ({balance_data.get('period')})",
            'severity': 'high',
            'fix': 'Asegurarse de que ambos documentos correspondan al mismo período contable.'
        })
    
    # Verificar que la utilidad neta coincida con la utilidad del período en el balance
    pl_net_income = None
    for item in pl_data.get('totals', {}).items():
        if 'utilidad' in item[0].lower() or 'net' in item[0].lower():
            pl_net_income = item[1]
            break
    
    balance_net_income = None
    for item in balance_data.get('capital_contable', []):
        if 'utilidad' in item.name.lower() or 'net' in item.name.lower():
            balance_net_income = item.amount
            break
    
    if pl_net_income is not None and balance_net_income is not None:
        if abs(pl_net_income - balance_net_income) > Decimal('0.01'):
            discrepancies.append({
                'type': 'income_mismatch',
                'description': f"La utilidad neta no coincide: P&L (${pl_net_income}) vs Balance (${balance_net_income})",
                'severity': 'high',
                'fix': f"Ajustar la utilidad neta en el Balance General para que coincida con el P&L: ${pl_net_income}"
            })
    
    return discrepancies

def retrieve_financial_docs(repo_url: str, branch: str = "main") -> Dict[str, str]:
    """Recupera los documentos financieros del repositorio.

    Args:
        repo_url (str): URL del repositorio GitHub (formato: https://github.com/owner/repo)
        branch (str): Rama del repositorio a consultar (default: "main")

    Returns:
        Dict[str, str]: Diccionario con los contenidos de los documentos
            - 'pl': Contenido del documento P&L
            - 'balance': Contenido del documento Balance
    
    Raises:
        ValueError: Si hay errores al acceder al repositorio o los documentos
    """
    try:
        # Extraer owner y repo de la URL
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            raise ValueError("URL del repositorio inválida")
        
        owner, repo_name = match.groups()
        
        # Inicializar cliente de GitHub
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("Token de GitHub no encontrado en variables de entorno")
        
        g = Github(github_token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Buscar archivos financieros
        pl_files = []
        balance_files = []
        
        # Buscar en la rama especificada
        contents = repo.get_contents("", ref=branch)
        for content in contents:
            if content.type == "file":
                filename = content.name.lower()
                if any(ext in filename for ext in ['.md', '.csv']):
                    if 'pl' in filename or 'income' in filename or 'profit' in filename:
                        pl_files.append(content)
                    elif 'balance' in filename or 'bs' in filename:
                        balance_files.append(content)
        
        if not pl_files:
            raise ValueError("No se encontraron archivos de P&L")
        if not balance_files:
            raise ValueError("No se encontraron archivos de Balance General")
        
        # Obtener el contenido de los archivos más recientes
        pl_content = repo.get_contents(pl_files[0].path, ref=branch).decoded_content.decode('utf-8')
        balance_content = repo.get_contents(balance_files[0].path, ref=branch).decoded_content.decode('utf-8')
        
        return {
            'pl': pl_content,
            'balance': balance_content
        }
        
    except Exception as e:
        raise ValueError(f"Error al recuperar documentos: {str(e)}")

def create_github_issue(discrepancies: List[Dict[str, Any]], repo_url: str) -> str:
    """Crea o actualiza un issue en GitHub con las discrepancias encontradas.

    Args:
        discrepancies (List[Dict]): Lista de discrepancias encontradas
        repo_url (str): URL del repositorio GitHub

    Returns:
        str: URL del issue creado o actualizado
    """
    try:
        # Extraer owner y repo de la URL
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            raise ValueError("URL del repositorio inválida")
        
        owner, repo_name = match.groups()
        
        # Inicializar cliente de GitHub
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("Token de GitHub no encontrado en variables de entorno")
        
        g = Github(github_token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Crear título y cuerpo del issue
        title = f"Auditoría Financiera: {len(discrepancies)} discrepancias encontradas"
        
        # Agrupar discrepancias por severidad
        high_severity = [d for d in discrepancies if d['severity'] == 'high']
        medium_severity = [d for d in discrepancies if d['severity'] == 'medium']
        low_severity = [d for d in discrepancies if d['severity'] == 'low']
        
        body = "## 📊 Resumen de la Auditoría\n\n"
        body += f"- Total de discrepancias: {len(discrepancies)}\n"
        body += f"- Severidad Alta: {len(high_severity)}\n"
        body += f"- Severidad Media: {len(medium_severity)}\n"
        body += f"- Severidad Baja: {len(low_severity)}\n\n"
        
        if high_severity:
            body += "## 🔴 Discrepancias de Alta Severidad\n\n"
            for d in high_severity:
                body += f"### {d['type']}\n"
                body += f"**Descripción**: {d['description']}\n"
                body += f"**Propuesta de Corrección**: {d.get('fix', 'No hay propuesta específica.')}\n\n"
            body += "\n"
            
        if medium_severity:
            body += "## 🟡 Discrepancias de Severidad Media\n\n"
            for d in medium_severity:
                body += f"### {d['type']}\n"
                body += f"**Descripción**: {d['description']}\n"
                body += f"**Propuesta de Corrección**: {d.get('fix', 'No hay propuesta específica.')}\n\n"
            body += "\n"
            
        if low_severity:
            body += "## 🟢 Discrepancias de Baja Severidad\n\n"
            for d in low_severity:
                body += f"### {d['type']}\n"
                body += f"**Descripción**: {d['description']}\n"
                body += f"**Propuesta de Corrección**: {d.get('fix', 'No hay propuesta específica.')}\n\n"
            body += "\n"
        
        body += "\n## 📝 Recomendaciones Generales\n\n"
        body += "1. Revisar y validar todas las discrepancias encontradas\n"
        body += "2. Implementar las correcciones propuestas\n"
        body += "3. Ejecutar una nueva auditoría después de realizar las correcciones\n"
        body += "4. Considerar implementar controles adicionales para prevenir futuras discrepancias\n\n"
        
        body += "\n---\n"
        body += "Este issue fue generado automáticamente por el Agente Auditor Financiero.\n"
        body += f"Fecha de auditoría: {datetime.datetime.now(ZoneInfo('UTC')).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Buscar si ya existe un issue abierto con el mismo título
        existing_issues = repo.get_issues(state='open')
        for issue in existing_issues:
            if issue.title == title:
                # Actualizar issue existente
                issue.edit(body=body)
                return issue.html_url
        
        # Crear nuevo issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=['auditoría', 'finanzas', 'automático']
        )
        
        return issue.html_url
        
    except Exception as e:
        raise ValueError(f"Error al crear issue: {str(e)}")

def audit_financial_documents(repo_url: str, branch: str = "main") -> Dict[str, Any]:
    """Función principal que orquesta el proceso de auditoría."""
    try:
        # 1. Recuperar documentos
        docs = retrieve_financial_docs(repo_url, branch)
        
        # 2. Comparar documentos
        discrepancies = compare_documents(docs['pl'], docs['balance'])
        
        # 3. Crear/actualizar issue
        issue_url = create_github_issue(discrepancies, repo_url)
        
        return {
            "status": "success",
            "discrepancies": discrepancies,
            "issue_url": issue_url
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

class AuditorAgent(LlmAgent):
    """Agente principal para la auditoría financiera usando ADK."""
    
    def __init__(self):
        # Inicializar agente principal
        super().__init__(
            name="auditor_agent",
            model="gemini-2.0-flash",
            description="Agente principal para realizar auditorías financieras",
            instruction=MAIN_AGENT_PROMPT,
            tools=[
                FunctionTool(self.retrieve_documents),
                FunctionTool(self.analyze_documents),
                FunctionTool(self.report_findings)
            ]
        )
        
        # Inicializar servicios y agentes
        self._session_service = InMemorySessionService()
        self._runner = Runner()
        self._comparison_agent = ComparisonAgent()
        self._issue_manager = IssueManagerAgent()
    
    @property
    def comparison_agent(self) -> ComparisonAgent:
        """Obtiene el agente de comparación."""
        return self._comparison_agent
    
    @property
    def issue_manager(self) -> IssueManagerAgent:
        """Obtiene el agente de gestión de issues."""
        return self._issue_manager
    
    def retrieve_documents(self, repo_url: str, branch: str = "main") -> Dict[str, str]:
        """Recupera los documentos financieros del repositorio."""
        return retrieve_financial_docs(repo_url, branch)
    
    def analyze_documents(self, docs: Dict[str, str]) -> List[Dict]:
        """Analiza los documentos financieros usando el agente de comparación."""
        pl_data = self.comparison_agent.parse_content(docs['pl'])
        balance_data = self.comparison_agent.parse_content(docs['balance'])
        
        discrepancies = []
        
        # Comparar períodos
        period_discrepancy = self.comparison_agent.compare_periods(pl_data, balance_data)
        if period_discrepancy:
            discrepancies.append(period_discrepancy)
        
        # Comparar utilidad neta
        income_discrepancy = self.comparison_agent.compare_net_income(pl_data, balance_data)
        if income_discrepancy:
            discrepancies.append(income_discrepancy)
        
        # Analizar ratios
        ratio_discrepancies = self.comparison_agent.analyze_ratios(pl_data, balance_data)
        discrepancies.extend(ratio_discrepancies)
        
        return discrepancies
    
    def report_findings(self, discrepancies: List[Dict], repo_owner: str, repo_name: str) -> str:
        """Reporta los hallazgos usando el agente de gestión de issues."""
        return self.issue_manager.update_issue(discrepancies, repo_owner, repo_name)

def main():
    """Función principal que ejecuta la auditoría financiera."""
    print(f"Iniciando auditoría financiera - {datetime.datetime.now()}")
    
    try:
        # Construir URL del repositorio
        repo_owner = os.getenv('GITHUB_REPO_OWNER')
        repo_name = os.getenv('GITHUB_REPO_NAME')
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        
        # Inicializar agente principal
        auditor = AuditorAgent()
        
        # Ejecutar auditoría
        docs = auditor.retrieve_documents(repo_url, os.getenv('GITHUB_BRANCH', 'main'))
        discrepancies = auditor.analyze_documents(docs)
        
        if discrepancies:
            issue_url = auditor.report_findings(discrepancies, repo_owner, repo_name)
            print(f"Se encontraron {len(discrepancies)} discrepancias. Issue creado/actualizado: {issue_url}")
        else:
            print("No se encontraron discrepancias en los documentos financieros.")
            
    except Exception as e:
        print(f"Error durante la auditoría: {str(e)}")
        sys.exit(1)

# Crear el agente raíz para ADK
root_agent = LlmAgent(
    name="financial_auditor",
    model="gemini-2.0-flash",
    description="Agente para realizar auditorías financieras",
    instruction=MAIN_AGENT_PROMPT,
    tools=[
        FunctionTool(audit_financial_documents),
        FunctionTool(retrieve_financial_docs),
        FunctionTool(compare_documents),
        FunctionTool(create_github_issue)
    ]
)

if __name__ == "__main__":
    main()
