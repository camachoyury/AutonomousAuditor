import os
from dotenv import load_dotenv
from agent import retrieve_financial_docs

def test_retrieve_docs():
    print("Probando recuperación de documentos...")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # URL del repositorio
    repo_url = "https://github.com/camachoyury/financial-reports"
    branch = "main"
    
    print(f"Repositorio: {repo_url}")
    print(f"Rama: {branch}\n")
    
    try:
        # Intentar recuperar documentos
        docs = retrieve_financial_docs(repo_url, branch)
        
        # Mostrar contenido de los documentos
        print("Documentos recuperados exitosamente!")
        
        if 'pl' in docs:
            print("\nP&L (primeros 200 caracteres):")
            print(docs['pl'].content[:200])
        else:
            print("\nNo se encontró el documento P&L")
            
        if 'balance' in docs:
            print("\nBalance (primeros 200 caracteres):")
            print(docs['balance'].content[:200])
        else:
            print("\nNo se encontró el documento de Balance")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_retrieve_docs() 