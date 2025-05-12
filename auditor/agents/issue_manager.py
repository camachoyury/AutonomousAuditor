from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, List, Optional
from datetime import datetime
from github import Github
import os
from dotenv import load_dotenv
from auditor.core.prompts import REPORT_PROMPTS

class IssueManagerAgent(Agent):
    """Agente especializado en gestionar issues de GitHub usando ADK."""
    
    def __init__(self):
        super().__init__(
            name="issue_manager",
            model="gemini-2.0-flash",
            description="Agente para gestionar issues de GitHub con discrepancias financieras",
            tools=[
                FunctionTool(self.create_issue),
                FunctionTool(self.update_issue),
                FunctionTool(self.format_issue_body)
            ]
        )
        
        # Inicializar cliente de GitHub
        load_dotenv()
        self._github_token = os.getenv('GITHUB_TOKEN')
        if not self._github_token:
            raise ValueError("Token de GitHub no encontrado")
        self._github = Github(self._github_token)
    
    def create_issue(self, discrepancies: List[Dict], repo_owner: str, repo_name: str) -> str:
        """Crea un nuevo issue en GitHub."""
        try:
            repo = self._github.get_repo(f"{repo_owner}/{repo_name}")
            
            title = REPORT_PROMPTS['issue_title'].format(
                period="Q1 2024",
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
            body = self.format_issue_body(discrepancies)
            
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=['auditoría', 'finanzas', 'automático']
            )
            
            return issue.html_url
            
        except Exception as e:
            raise ValueError(f"Error al crear issue: {str(e)}")
    
    def update_issue(self, discrepancies: List[Dict], repo_owner: str, repo_name: str) -> str:
        """Actualiza un issue existente en GitHub."""
        try:
            repo = self._github.get_repo(f"{repo_owner}/{repo_name}")
            
            title = REPORT_PROMPTS['issue_title'].format(
                period="Q1 2024",
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
            body = self.format_issue_body(discrepancies)
            
            # Buscar issue existente
            existing_issues = repo.get_issues(state='open')
            for issue in existing_issues:
                if issue.title == title:
                    issue.edit(body=body)
                    return issue.html_url
            
            # Si no existe, crear uno nuevo
            return self.create_issue(discrepancies, repo_owner, repo_name)
            
        except Exception as e:
            raise ValueError(f"Error al actualizar issue: {str(e)}")
    
    def format_issue_body(self, discrepancies: List[Dict]) -> str:
        """Formatea el cuerpo del issue con las discrepancias encontradas."""
        # Agrupar discrepancias por severidad
        high_severity = [d for d in discrepancies if d['severity'] == 'high']
        medium_severity = [d for d in discrepancies if d['severity'] == 'medium']
        low_severity = [d for d in discrepancies if d['severity'] == 'low']
        
        # Generar secciones de severidad
        severity_sections = ""
        if high_severity:
            severity_sections += "\n### 🔴 Discrepancias de Alta Severidad\n"
            for d in high_severity:
                severity_sections += f"- {d['description']}\n"
                if 'fix' in d:
                    severity_sections += f"  - **Propuesta de Corrección**: {d['fix']}\n"
        
        if medium_severity:
            severity_sections += "\n### 🟡 Discrepancias de Severidad Media\n"
            for d in medium_severity:
                severity_sections += f"- {d['description']}\n"
                if 'fix' in d:
                    severity_sections += f"  - **Propuesta de Corrección**: {d['fix']}\n"
        
        if low_severity:
            severity_sections += "\n### 🟢 Discrepancias de Baja Severidad\n"
            for d in low_severity:
                severity_sections += f"- {d['description']}\n"
                if 'fix' in d:
                    severity_sections += f"  - **Propuesta de Corrección**: {d['fix']}\n"
        
        # Generar recomendaciones
        recommendations = """
- Revisar y validar todas las discrepancias encontradas
- Implementar las correcciones propuestas
- Ejecutar una nueva auditoría después de las correcciones
- Considerar implementar controles adicionales para prevenir futuras discrepancias
"""
        
        # Crear cuerpo del issue
        return REPORT_PROMPTS['issue_body'].format(
            period="Q1 2024",
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_discrepancies=len(discrepancies),
            severity_sections=severity_sections,
            recommendations=recommendations
        ) 