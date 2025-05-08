from google.adk import Agent, Tool
from typing import List, Dict, Optional
from github import Github
import os
from datetime import datetime

class IssueManagerAgent(Agent):
    """Agente especializado en gestionar issues de GitHub para reportar discrepancias."""
    
    def __init__(self):
        super().__init__()
        self.github_client = Github(os.getenv('GITHUB_TOKEN'))
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER')
        self.repo_name = os.getenv('GITHUB_REPO_NAME')
        self.repo = self.github_client.get_user(self.repo_owner).get_repo(self.repo_name)
    
    @Tool
    def create_or_update_issue(self, discrepancies: List[Dict], period: str) -> str:
        """Crea o actualiza un issue de GitHub con las discrepancias encontradas.
        
        Args:
            discrepancies (List[Dict]): Lista de discrepancias encontradas
            period (str): Período de los reportes financieros
        
        Returns:
            str: URL del issue creado o actualizado
        """
        if not discrepancies:
            return "No se encontraron discrepancias que reportar."
        
        # Crear título y cuerpo del issue
        title = f"Discrepancias Financieras - {period}"
        
        # Organizar discrepancias por severidad
        high_severity = [d for d in discrepancies if d['severity'] == 'high']
        medium_severity = [d for d in discrepancies if d['severity'] == 'medium']
        low_severity = [d for d in discrepancies if d['severity'] == 'low']
        
        body = f"""# Auditoría Financiera - {period}

## Resumen
Se encontraron {len(discrepancias)} discrepancias en los reportes financieros:
- {len(high_severity)} de alta severidad
- {len(medium_severity)} de severidad media
- {len(low_severity)} de baja severidad

## Discrepancias de Alta Severidad
"""
        
        if high_severity:
            for d in high_severity:
                body += f"- ❌ {d['description']}\n"
        else:
            body += "- No se encontraron discrepancias de alta severidad\n"
        
        body += "\n## Discrepancias de Severidad Media\n"
        if medium_severity:
            for d in medium_severity:
                body += f"- ⚠️ {d['description']}\n"
        else:
            body += "- No se encontraron discrepancias de severidad media\n"
        
        body += "\n## Discrepancias de Baja Severidad\n"
        if low_severity:
            for d in low_severity:
                body += f"- ℹ️ {d['description']}\n"
        else:
            body += "- No se encontraron discrepancias de baja severidad\n"
        
        body += f"\n---\nÚltima actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Buscar si ya existe un issue para este período
        existing_issue = None
        for issue in self.repo.get_issues(state='open'):
            if issue.title == title:
                existing_issue = issue
                break
        
        if existing_issue:
            # Actualizar issue existente
            existing_issue.edit(body=body)
            return existing_issue.html_url
        else:
            # Crear nuevo issue
            new_issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=['auditoría', 'finanzas', 'discrepancia']
            )
            return new_issue.html_url 