import os
from github import Github
from dotenv import load_dotenv

def test_github_connection():
    """Prueba la conexión con GitHub y la recuperación de archivos."""
    print("\n=== Probando Conexión con GitHub ===\n")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar token
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ Error: No se encontró el token de GitHub")
        return False
    
    try:
        # Inicializar cliente de GitHub
        g = Github(token)
        
        # Obtener repositorio
        repo_owner = os.getenv('GITHUB_REPO_OWNER', 'camachoyury')
        repo_name = os.getenv('GITHUB_REPO_NAME', 'financial-reports')
        repo = g.get_repo(f"{repo_owner}/{repo_name}")
        
        print(f"✅ Conexión exitosa con el repositorio: {repo_owner}/{repo_name}")
        
        # Listar archivos en el repositorio
        print("\n📁 Archivos encontrados:")
        contents = repo.get_contents("")
        for content in contents:
            if content.type == "file":
                print(f"- {content.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_github_connection()
    exit(0 if success else 1) 