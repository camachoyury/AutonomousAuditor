import os
from typing import Dict, List, Tuple
from github import Github
from github.ContentFile import ContentFile

from ..core.models import FinancialDocument
from ..core.exceptions import GitHubError, ConfigurationError
from ..core.constants import (
    FORMAT_MARKDOWN, FORMAT_CSV,
    FILE_EXTENSIONS, PL_FILE_PATTERNS, BALANCE_FILE_PATTERNS,
    GITHUB_DEFAULT_BRANCH, GITHUB_LABELS
)

class GitHubService:
    """Servicio para interactuar con GitHub."""
    
    def __init__(self):
        """Inicializa el servicio de GitHub."""
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ConfigurationError("No se encontró el token de GitHub")
        
        self.github_client = Github(token)
    
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """Parsea la URL del repositorio para obtener owner y nombre."""
        try:
            # Remover protocolo y dominio
            path = repo_url.split('github.com/')[-1]
            # Remover .git si existe
            path = path.replace('.git', '')
            # Dividir en owner y repo
            owner, repo = path.split('/')
            return owner, repo
        except Exception:
            raise GitHubError(f"URL de repositorio inválida: {repo_url}")
    
    def retrieve_documents(self, repo_url: str, branch: str = GITHUB_DEFAULT_BRANCH) -> Dict[str, FinancialDocument]:
        """Recupera los documentos financieros del repositorio."""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            
            pl_files = []
            balance_files = []
            
            contents = repo.get_contents("", ref=branch)
            for content in contents:
                if content.type == "file":
                    filename = content.name.lower()
                    if any(ext in filename for ext in FILE_EXTENSIONS):
                        if any(pattern in filename for pattern in PL_FILE_PATTERNS):
                            pl_files.append(content)
                        elif any(pattern in filename for pattern in BALANCE_FILE_PATTERNS):
                            balance_files.append(content)
            
            if not pl_files:
                raise GitHubError("No se encontraron archivos de P&L")
            if not balance_files:
                raise GitHubError("No se encontraron archivos de Balance General")
            
            pl_content = repo.get_contents(pl_files[0].path, ref=branch).decoded_content.decode('utf-8')
            balance_content = repo.get_contents(balance_files[0].path, ref=branch).decoded_content.decode('utf-8')
            
            return {
                'pl': FinancialDocument(
                    content=pl_content,
                    doc_type='pl',
                    file_format=FORMAT_MARKDOWN if pl_content.strip().startswith('|') else FORMAT_CSV
                ),
                'balance': FinancialDocument(
                    content=balance_content,
                    doc_type='balance',
                    file_format=FORMAT_MARKDOWN if balance_content.strip().startswith('|') else FORMAT_CSV
                )
            }
            
        except Exception as e:
            raise GitHubError(f"Error al recuperar documentos: {str(e)}")
    
    def create_or_update_issue(self, discrepancies: List[Dict], repo_url: str) -> str:
        """Crea o actualiza un issue en GitHub con las discrepancias encontradas."""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            
            title = f"Auditoría Financiera: {len(discrepancies)} discrepancias encontradas"
            
            high_severity = [d for d in discrepancies if d['severity'] == 'high']
            medium_severity = [d for d in discrepancies if d['severity'] == 'medium']
            low_severity = [d for d in discrepancies if d['severity'] == 'low']
            
            body = self._generate_issue_body(high_severity, medium_severity, low_severity)
            
            # Buscar issue existente
            existing_issues = repo.get_issues(state='open')
            for issue in existing_issues:
                if issue.title == title:
                    issue.edit(body=body)
                    return issue.html_url
            
            # Crear nuevo issue
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=GITHUB_LABELS
            )
            
            return issue.html_url
            
        except Exception as e:
            raise GitHubError(f"Error al crear/actualizar issue: {str(e)}")
    
    def _generate_issue_body(self, high_severity: List[Dict], medium_severity: List[Dict], low_severity: List[Dict]) -> str:
        """Genera el cuerpo del issue con las discrepancias encontradas."""
        body = "# Resultados de la Auditoría Financiera\n\n"
        
        if high_severity:
            body += "## 🔴 Discrepancias de Alta Severidad\n\n"
            for d in high_severity:
                body += f"### {d['type']}\n"
                body += f"- **Descripción**: {d['description']}\n"
                body += f"- **Solución**: {d['fix']}\n\n"
        
        if medium_severity:
            body += "## 🟡 Discrepancias de Severidad Media\n\n"
            for d in medium_severity:
                body += f"### {d['type']}\n"
                body += f"- **Descripción**: {d['description']}\n"
                body += f"- **Solución**: {d['fix']}\n\n"
        
        if low_severity:
            body += "## 🟢 Discrepancias de Baja Severidad\n\n"
            for d in low_severity:
                body += f"### {d['type']}\n"
                body += f"- **Descripción**: {d['description']}\n"
                body += f"- **Solución**: {d['fix']}\n\n"
        
        return body 