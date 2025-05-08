from google.adk.tools import Tool
from google.adk.agents import Agent
from typing import Dict, List
import os
from github import Github
from dotenv import load_dotenv

class DocumentRetrieverAgent(Agent):
    """Agente especializado en recuperar documentos financieros de GitHub."""
    
    def __init__(self):
        super().__init__()
        self.github_client = None
        self._initialize_github()
    
    def _initialize_github(self):
        """Inicializa el cliente de GitHub con el token."""
        load_dotenv()
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("Token de GitHub no encontrado en variables de entorno")
        self.github_client = Github(token)
    
    @Tool
    async def retrieve_documents(self, repo_url: str, branch: str = "main") -> Dict:
        """Recupera los documentos financieros del repositorio.
        
        Args:
            repo_url (str): URL del repositorio GitHub
            branch (str): Rama del repositorio a consultar
        
        Returns:
            Dict: Diccionario con los documentos recuperados
        """
        try:
            # Extraer owner y repo de la URL
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            
            # Buscar archivos financieros
            pl_files = []
            balance_files = []
            
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
            
            # Obtener contenido de los archivos más recientes
            pl_content = repo.get_contents(pl_files[0].path, ref=branch).decoded_content.decode('utf-8')
            balance_content = repo.get_contents(balance_files[0].path, ref=branch).decoded_content.decode('utf-8')
            
            return {
                'pl': {
                    'content': pl_content,
                    'format': self._detect_format(pl_content),
                    'filename': pl_files[0].name
                },
                'balance': {
                    'content': balance_content,
                    'format': self._detect_format(balance_content),
                    'filename': balance_files[0].name
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error al recuperar documentos: {str(e)}")
    
    def _parse_repo_url(self, repo_url: str) -> tuple:
        """Extrae el owner y nombre del repositorio de la URL."""
        import re
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            raise ValueError("URL del repositorio inválida")
        return match.groups()
    
    def _detect_format(self, content: str) -> str:
        """Detecta si el documento es Markdown o CSV."""
        if content.strip().startswith('|') or content.strip().startswith('#'):
            return 'markdown'
        return 'csv' 