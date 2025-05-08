import os
import asyncio
from fastapi import FastAPI, Request
import uvicorn
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, List
from auditor.agent import audit_financial_documents
import hmac
import hashlib

# Crear la aplicación FastAPI
app = FastAPI(title="Auditor Financiero")

# Definir la función de auditoría
async def run_audit(repo_url: str, branch: str = "main") -> Dict:
    """Ejecuta una auditoría financiera.
    
    Args:
        repo_url (str): URL del repositorio GitHub a auditar
        branch (str): Rama del repositorio a auditar (default: "main")
        
    Returns:
        Dict: Resultado de la auditoría con el estado y las discrepancias encontradas
    """
    try:
        result = audit_financial_documents(repo_url, branch)
        return result
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

# Crear el agente LLM
root_agent = LlmAgent(
    name="financial_auditor",
    model="gemini-2.0-flash",
    description="Agente para realizar auditorías financieras",
    instruction="""Soy un agente especializado en auditoría financiera. 
    Mi tarea es analizar documentos financieros y detectar discrepancias.
    Puedo recuperar documentos de GitHub, analizarlos y crear issues con los hallazgos.""",
    tools=[FunctionTool(run_audit)]
)

# Crear servicio de sesiones
session_service = InMemorySessionService()

# Crear el runner
runner = Runner(
    agent=root_agent,
    app_name="financial_auditor",
    session_service=session_service
)

async def verify_github_webhook(request: Request) -> bool:
    """Verifica la firma del webhook de GitHub."""
    if 'X-Hub-Signature-256' not in request.headers:
        return False
    
    signature = request.headers['X-Hub-Signature-256']
    secret = os.getenv('GITHUB_WEBHOOK_SECRET', '').encode()
    body = await request.body()
    
    expected_signature = 'sha256=' + hmac.new(
        secret,
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.post("/webhook/github")
async def github_webhook(request: Request):
    """Endpoint para el webhook de GitHub."""
    if not await verify_github_webhook(request):
        return {"status": "error", "message": "Invalid signature"}
    
    payload = await request.json()
    
    # Verificar si es un push a main
    if (payload.get('ref') == 'refs/heads/main' and 
        payload.get('repository', {}).get('html_url')):
        
        repo_url = payload['repository']['html_url']
        result = await run_audit(repo_url=repo_url, branch='main')
        return result
    
    return {"status": "skipped", "message": "Not a push to main"}

@app.post("/audit")
async def audit_endpoint(repo_url: str, branch: str = "main"):
    """Ejecuta una auditoría financiera."""
    session = session_service.create_session(
        app_name="financial_auditor",
        user_id="default_user",
        session_id="audit_session"
    )
    
    result = await run_audit(repo_url=repo_url, branch=branch)
    return result

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")

if __name__ == "__main__":
    main() 