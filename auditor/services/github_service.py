import os
from typing import Dict, List, Optional, Tuple
from github import Auth, Github
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
        
        self.github_client = Github(auth=Auth.Token(token))
    
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
    
    @staticmethod
    def _detect_format(filename: str) -> str:
        """El formato se deduce de la extensión del archivo."""
        return FORMAT_CSV if filename.lower().endswith('.csv') else FORMAT_MARKDOWN

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
            
            pl_file = repo.get_contents(pl_files[0].path, ref=branch)
            balance_file = repo.get_contents(balance_files[0].path, ref=branch)
            pl_content = pl_file.decoded_content.decode('utf-8')
            balance_content = balance_file.decoded_content.decode('utf-8')
            
            return {
                'pl': FinancialDocument(
                    content=pl_content,
                    doc_type='pl',
                    file_format=self._detect_format(pl_files[0].name)
                ),
                'balance': FinancialDocument(
                    content=balance_content,
                    doc_type='balance',
                    file_format=self._detect_format(balance_files[0].name)
                )
            }
            
        except Exception as e:
            raise GitHubError(f"Error al recuperar documentos: {str(e)}")
    
    def create_or_update_issue(self, discrepancies: List[Dict], repo_url: str, period: Optional[str] = None) -> str:
        """Crea o actualiza el issue de auditoría del período (un issue abierto por período)."""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")

            # Título estable: así la siguiente auditoría actualiza el issue en vez de duplicarlo.
            title = f"Auditoría Financiera - {period}" if period else "Auditoría Financiera"
            body = self._generate_issue_body(discrepancies)

            for issue in repo.get_issues(state='open'):
                if issue.title == title:
                    issue.edit(body=body)
                    return issue.html_url

            issue = repo.create_issue(title=title, body=body, labels=GITHUB_LABELS)
            return issue.html_url

        except Exception as e:
            raise GitHubError(f"Error al crear/actualizar issue: {str(e)}")

    @staticmethod
    def _generate_issue_body(discrepancies: List[Dict]) -> str:
        """Genera el cuerpo del issue agrupando las discrepancias por severidad."""
        sections = [
            ('high', '🔴 Discrepancias de Alta Severidad'),
            ('medium', '🟡 Discrepancias de Severidad Media'),
            ('low', '🟢 Discrepancias de Baja Severidad'),
        ]
        body = "# Resultados de la Auditoría Financiera\n\n"
        body += f"Total de discrepancias: **{len(discrepancies)}**\n\n"
        for severity, heading in sections:
            items = [d for d in discrepancies if d.get('severity') == severity]
            if not items:
                continue
            body += f"## {heading}\n\n"
            for d in items:
                origin = "🤖 Gemini" if d.get('source') == 'gemini' else "📐 Regla"
                body += f"### {d['type']} ({origin})\n"
                body += f"- **Descripción**: {d['description']}\n"
                body += f"- **Solución**: {d.get('fix', 'No hay propuesta específica.')}\n\n"
        body += "---\nGenerado automáticamente por Autonomous Financial Auditor.\n"
        return body
