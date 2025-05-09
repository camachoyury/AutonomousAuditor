import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from ..agent import audit_financial_documents

def test_audit_flow():
    """Prueba el flujo completo de auditoría financiera."""
    print("\n=== Probando Flujo de Auditoría Financiera ===\n")
    
    # 1. Cargar variables de entorno
    load_dotenv()
    
    # 2. Verificar variables de entorno necesarias
    required_vars = [
        'GITHUB_TOKEN',
        'GITHUB_REPO_OWNER',
        'GITHUB_REPO_NAME',
        'GITHUB_BRANCH'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Faltan las siguientes variables de entorno:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Variables de entorno verificadas")
    
    # 3. Construir URL del repositorio
    repo_url = f"https://github.com/{os.getenv('GITHUB_REPO_OWNER')}/{os.getenv('GITHUB_REPO_NAME')}"
    print(f"\n📦 Repositorio a auditar: {repo_url}")
    
    # 4. Ejecutar auditoría
    print("\n🔍 Ejecutando auditoría...")
    try:
        result = audit_financial_documents(repo_url, os.getenv('GITHUB_BRANCH'))
        
        if result["status"] == "success":
            print("\n✅ Auditoría completada exitosamente")
            print(f"\n📊 Resultados:")
            print(f"- Total discrepancias: {len(result['discrepancies'])}")
            print(f"- URL del issue: {result['issue_url']}")
            
            if result['discrepancies']:
                print("\n🔍 Discrepancias encontradas:")
                for d in result['discrepancies']:
                    print(f"\n- Tipo: {d['type']}")
                    print(f"  Descripción: {d['description']}")
                    print(f"  Severidad: {d['severity']}")
                    if 'fix' in d:
                        print(f"  Corrección: {d['fix']}")
        else:
            print(f"\n❌ Error en la auditoría: {result['error_message']}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error durante la auditoría: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_audit_flow()
    sys.exit(0 if success else 1) 