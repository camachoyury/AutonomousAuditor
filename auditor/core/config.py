"""Configuración del auditor, leída de variables de entorno."""

import os

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def gemini_model() -> str:
    """Modelo Gemini a usar (variable GEMINI_MODEL)."""
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def llm_enabled() -> bool:
    """El análisis con Gemini está activo si hay credenciales y no se desactivó.

    Se activa con GOOGLE_API_KEY (Gemini API) o GOOGLE_GENAI_USE_VERTEXAI=true (Vertex AI).
    Se desactiva explícitamente con AUDITOR_USE_LLM=false.
    """
    if os.getenv("AUDITOR_USE_LLM", "true").strip().lower() in ("0", "false", "no"):
        return False
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return True
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() in ("1", "true")
