from google.adk.tools import Tool
from google.adk.agents import Agent
from typing import Dict, List
from .document_retriever import DocumentRetrieverAgent
from .document_parser import DocumentParserAgent
from .comparison_agent import ComparisonAgent
from .issue_manager import IssueManagerAgent

class FinancialAuditWorkflow(Agent):
    """Agente de flujo de trabajo que orquesta el proceso de auditoría financiera.
    
    Este agente actúa como coordinador principal, delegando tareas específicas a agentes especializados:
    - DocumentRetrieverAgent: Para obtener documentos de GitHub
    - DocumentParserAgent: Para parsear documentos financieros
    - ComparisonAgent: Para comparar y detectar discrepancias
    - IssueManagerAgent: Para gestionar issues de GitHub
    """
    
    def __init__(self):
        super().__init__()
        self.document_retriever = DocumentRetrieverAgent()
        self.document_parser = DocumentParserAgent()
        self.comparison_agent = ComparisonAgent()
        self.issue_manager = IssueManagerAgent()
    
    @Tool
    async def run_audit(self, repo_url: str, branch: str = 'main') -> Dict:
        """Ejecuta el proceso completo de auditoría financiera.
        
        Args:
            repo_url (str): URL del repositorio de GitHub
            branch (str): Rama del repositorio a auditar
        
        Returns:
            Dict: Resultados de la auditoría
        """
        try:
            # 1. Obtener documentos usando DocumentRetrieverAgent
            print("Obteniendo documentos financieros...")
            docs = await self.document_retriever.retrieve_documents(repo_url, branch)
            
            # 2. Parsear documentos usando DocumentParserAgent
            print("Parseando documentos...")
            pl_data = await self.document_parser.parse_pl(docs['pl']['content'], docs['pl']['format'])
            balance_data = await self.document_parser.parse_balance(docs['balance']['content'], docs['balance']['format'])
            
            # 3. Comparar documentos usando ComparisonAgent
            print("Comparando documentos...")
            discrepancies = await self.comparison_agent.compare_documents(pl_data, balance_data)
            
            # 4. Crear/actualizar issue usando IssueManagerAgent
            print("Creando/actualizando issue...")
            period = pl_data.get('period', 'Período Desconocido')
            issue_url = await self.issue_manager.create_or_update_issue(discrepancies, period)
            
            return {
                'status': 'success',
                'period': period,
                'discrepancies_found': len(discrepancies),
                'issue_url': issue_url,
                'discrepancies': discrepancies
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @Tool
    async def get_audit_summary(self, audit_result: Dict) -> str:
        """Genera un resumen legible de los resultados de la auditoría.
        
        Args:
            audit_result (Dict): Resultados de la auditoría
        
        Returns:
            str: Resumen formateado
        """
        if audit_result['status'] == 'error':
            return f"❌ Error en la auditoría: {audit_result['error']}"
        
        summary = f"""# Resumen de Auditoría - {audit_result['period']}

## Estado: ✅ Completado

## Resultados:
- Discrepancias encontradas: {audit_result['discrepancies_found']}
- Issue de GitHub: {audit_result['issue_url']}

## Detalles de Discrepancias:
"""
        
        if audit_result['discrepancies']:
            for d in audit_result['discrepancies']:
                severity_emoji = {
                    'high': '❌',
                    'medium': '⚠️',
                    'low': 'ℹ️'
                }.get(d['severity'], '❓')
                
                summary += f"\n{severity_emoji} {d['description']}"
        else:
            summary += "\n✅ No se encontraron discrepancias."
        
        return summary 