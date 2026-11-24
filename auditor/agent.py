"""Punto de entrada de la auditoría: `python -m auditor.agent`."""

import logging
import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from .services.audit_service import AuditService

logger = logging.getLogger(__name__)


def audit_financial_documents(repo_url: str, branch: str = "main", service: Optional[AuditService] = None) -> Dict[str, Any]:
    """Ejecuta una auditoría y devuelve el resultado como diccionario serializable."""
    result = (service or AuditService()).run_audit(repo_url, branch)
    return {
        "status": result.status,
        "discrepancies": result.discrepancies,
        "issue_url": result.issue_url,
        "llm_used": result.llm_used,
        "llm_error": result.llm_error,
        "error_message": result.error_message,
    }


def main() -> None:
    """Audita el repositorio definido en GITHUB_REPO_OWNER / GITHUB_REPO_NAME / GITHUB_BRANCH."""
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    owner, name = os.getenv("GITHUB_REPO_OWNER"), os.getenv("GITHUB_REPO_NAME")
    if not owner or not name:
        logger.error("Define GITHUB_REPO_OWNER y GITHUB_REPO_NAME")
        sys.exit(2)

    result = audit_financial_documents(f"https://github.com/{owner}/{name}", os.getenv("GITHUB_BRANCH", "main"))
    if result["status"] != "success":
        logger.error("Auditoría fallida: %s", result["error_message"])
        sys.exit(1)

    logger.info("Gemini: %s", "usado" if result["llm_used"] else f"no usado ({result['llm_error'] or 'desactivado'})")
    if result["discrepancies"]:
        logger.info("%d discrepancias. Issue: %s", len(result["discrepancies"]), result["issue_url"])
    else:
        logger.info("No se encontraron discrepancias.")


if __name__ == "__main__":
    main()
