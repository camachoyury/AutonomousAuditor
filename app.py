"""API del Auditor Financiero: webhook de GitHub y endpoint manual de auditoría."""

import hashlib
import hmac
import logging
import os
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from auditor.agent import audit_financial_documents
from auditor.utils.validators import validate_repo_url

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("auditor.api")

app = FastAPI(title="Auditor Financiero")


def _verify_signature(body: bytes, signature: str | None) -> bool:
    """Valida la firma HMAC-SHA256 del webhook. Sin secreto configurado, rechaza todo."""
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def _background_audit(repo_url: str, branch: str) -> None:
    result = audit_financial_documents(repo_url, branch)
    logger.info("Auditoría de %s: %s (%d discrepancias)", repo_url, result["status"], len(result["discrepancies"]))


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/github", status_code=202)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
) -> Dict[str, str]:
    """Recibe el webhook de push de GitHub; la auditoría corre en segundo plano
    (GitHub exige respuesta en menos de 10 s y la llamada a Gemini puede tardar más)."""
    body = await request.body()
    if not _verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Firma inválida")

    payload: Dict[str, Any] = await request.json()
    repo_url = payload.get("repository", {}).get("html_url")
    default_branch = payload.get("repository", {}).get("default_branch", "main")
    if not repo_url or payload.get("ref") != f"refs/heads/{default_branch}":
        return {"status": "skipped", "message": "No es un push a la rama principal"}

    background_tasks.add_task(_background_audit, repo_url, default_branch)
    return {"status": "accepted"}


@app.post("/audit")
def audit_endpoint(repo_url: str, branch: str = "main", x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    """Auditoría manual. Requiere la cabecera X-API-Key igual a AUDIT_API_KEY."""
    expected = os.getenv("AUDIT_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="AUDIT_API_KEY no está configurada")
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="API key inválida")
    if not validate_repo_url(repo_url):
        raise HTTPException(status_code=422, detail="URL de repositorio inválida")
    return audit_financial_documents(repo_url, branch)


def main() -> None:
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
