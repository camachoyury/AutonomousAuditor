"""Revisión de los estados financieros con Gemini a través de Google ADK."""

import asyncio
import json
import logging
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from ..core.config import gemini_model, llm_enabled
from ..core.exceptions import LLMError
from ..core.prompts import AUDITOR_INSTRUCTION, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

APP_NAME = "financial_auditor"
USER_ID = "auditor"


class LLMFinding(BaseModel):
    """Un hallazgo reportado por el modelo."""

    type: str = Field(description="Identificador corto en snake_case")
    description: str = Field(description="Qué está mal, citando los montos exactos")
    severity: Literal["high", "medium", "low"]
    fix: str = Field(description="Corrección propuesta")


class LLMAuditReport(BaseModel):
    """Salida estructurada del agente auditor."""

    findings: List[LLMFinding] = Field(default_factory=list)


def _to_jsonable(value: Any) -> Any:
    """Convierte Decimal, dataclasses, etc. a tipos serializables en JSON."""
    if isinstance(value, Decimal):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


class LLMAuditService:
    """Agente ADK (Gemini) que revisa P&L y Balance y devuelve hallazgos estructurados."""

    def __init__(self, model: Optional[str] = None, enabled: Optional[bool] = None) -> None:
        self.model = model or gemini_model()
        self.enabled = llm_enabled() if enabled is None else enabled

    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            name="financial_auditor",
            model=self.model,
            description="Auditor financiero que revisa un P&L contra un Balance General",
            instruction=AUDITOR_INSTRUCTION,
            output_schema=LLMAuditReport,
            generate_content_config=types.GenerateContentConfig(temperature=0.0),
        )

    def review(
        self,
        pl_data: Dict[str, Any],
        balance_data: Dict[str, Any],
        rule_findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Revisa los documentos con Gemini. Devuelve discrepancias en el mismo formato que las reglas.

        Es síncrono para poder usarse desde servicios y endpoints sin bucle de eventos.
        No usar dentro de una corrutina en ejecución.
        """
        if not self.enabled:
            return []
        return asyncio.run(self.areview(pl_data, balance_data, rule_findings))

    async def areview(
        self,
        pl_data: Dict[str, Any],
        balance_data: Dict[str, Any],
        rule_findings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        payload = json.dumps(
            _to_jsonable({
                "pl": pl_data,
                "balance": balance_data,
                "hallazgos_reglas": [
                    {"type": f.get("type"), "description": f.get("description")}
                    for f in rule_findings
                ],
            }),
            ensure_ascii=False,
            indent=2,
        )
        message = types.Content(
            role="user",
            parts=[types.Part(text=USER_PROMPT_TEMPLATE.format(payload=payload))],
        )

        session_service = InMemorySessionService()
        runner = Runner(
            agent=self._build_agent(),
            app_name=APP_NAME,
            session_service=session_service,
        )
        session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

        final_text = ""
        try:
            async for event in runner.run_async(
                user_id=USER_ID, session_id=session.id, new_message=message
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = "".join(p.text or "" for p in event.content.parts)
        except Exception as exc:
            raise LLMError(f"Error al consultar Gemini ({self.model}): {exc}") from exc

        return self.parse_response(final_text)

    @staticmethod
    def parse_response(text: str) -> List[Dict[str, Any]]:
        """Valida la respuesta del modelo y la convierte al formato de discrepancias."""
        if not text.strip():
            raise LLMError("Gemini devolvió una respuesta vacía")
        try:
            report = LLMAuditReport.model_validate_json(text)
        except Exception as exc:
            raise LLMError(f"Respuesta de Gemini inválida: {exc}") from exc

        return [
            {
                "type": f"llm_{f.type}" if not f.type.startswith("llm_") else f.type,
                "description": f.description,
                "severity": f.severity,
                "fix": f.fix,
                "source": "gemini",
            }
            for f in report.findings
        ]
