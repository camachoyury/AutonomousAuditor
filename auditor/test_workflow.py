import os
from dotenv import load_dotenv
from agents.workflow_agent import FinancialAuditWorkflow

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar variables requeridas
    required_vars = ['GITHUB_TOKEN', 'GITHUB_REPO_OWNER', 'GITHUB_REPO_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Error: Faltan las siguientes variables de entorno: {', '.join(missing_vars)}")
        return
    
    # Construir URL del repositorio
    repo_owner = os.getenv('GITHUB_REPO_OWNER')
    repo_name = os.getenv('GITHUB_REPO_NAME')
    repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    
    # Obtener rama (default: main)
    branch = os.getenv('GITHUB_BRANCH', 'main')
    
    print(f"🚀 Iniciando auditoría financiera...")
    print(f"📁 Repositorio: {repo_url}")
    print(f"🌿 Rama: {branch}")
    print("-" * 50)
    
    # Crear y ejecutar el flujo de trabajo
    workflow = FinancialAuditWorkflow()
    audit_result = workflow.run_audit(repo_url, branch)
    
    # Generar y mostrar resumen
    summary = workflow.get_audit_summary(audit_result)
    print("\n" + summary)

if __name__ == "__main__":
    main() 