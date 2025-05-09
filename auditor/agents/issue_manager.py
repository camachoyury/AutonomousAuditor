from google.adk.tools.function_tool import FunctionTool as Tool
from google.adk.agents import Agent
from typing import Dict, List, Optional
from datetime import datetime
from github import Github
import os
from dotenv import load_dotenv
from auditor.core.prompts import REPORT_PROMPTS

class IssueManagerAgent:
    def __init__(self):
        self.agent = Agent(
            name="issue_manager",
            model="gemini-2.0-flash",
            description="Agente para gestionar issues de GitHub",
            tools=[Tool(self.create_or_update_issue)]
        )
        
        # Inicializar cliente de GitHub
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("Token de GitHub no encontrado")
        self.github = Github(self.github_token)
        
    def create_or_update_issue(self, discrepancies: List[Dict]) -> str:
        """Crea o actualiza un issue en GitHub con las discrepancias encontradas."""
        try:
            # Obtener repositorio
            repo_owner = os.getenv('GITHUB_REPO_OWNER')
            repo_name = os.getenv('GITHUB_REPO_NAME')
            repo = self.github.get_repo(f"{repo_owner}/{repo_name}")
            
            # Crear título y cuerpo del issue
            title = REPORT_PROMPTS['issue_title'].format(
                period="Q1 2024",
                date=datetime.now().strftime("%Y-%m-%d")
            )
            
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
            body = REPORT_PROMPTS['issue_body'].format(
                period="Q1 2024",
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_discrepancies=len(discrepancies),
                severity_sections=severity_sections,
                recommendations=recommendations
            )
            
            # Buscar issue existente o crear uno nuevo
            existing_issues = repo.get_issues(state='open')
            for issue in existing_issues:
                if issue.title == title:
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
            raise ValueError(f"Error al crear/actualizar issue: {str(e)}") 