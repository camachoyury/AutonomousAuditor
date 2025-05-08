import os
from dotenv import load_dotenv
from agent import audit_financial_documents

def test_audit():
    print("Iniciando auditoría financiera...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # URL del repositorio
    repo_url = "https://github.com/camachoyury/financial-reports"
    branch = "main"
    
    print(f"Repositorio: {repo_url}")
    print(f"Rama: {branch}\n")
    
    try:
        # Ejecutar auditoría
        result = audit_financial_documents(repo_url, branch)
        
        if result['status'] == 'success':
            print("✅ Auditoría completada exitosamente!")
            print(f"\nDiscrepancias encontradas: {len(result['discrepancies'])}")
            
            if result['discrepancies']:
                print("\nDetalles de las discrepancias:")
                for d in result['discrepancies']:
                    severity_emoji = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(d['severity'], '⚪')
                    
                    print(f"\n{severity_emoji} {d['description']}")
            
            print(f"\nIssue creado/actualizado: {result['issue_url']}")
        else:
            print(f"❌ Error en la auditoría: {result['error_message']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_audit() 