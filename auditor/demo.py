"""Demo local: audita un P&L y un Balance de una carpeta, sin GitHub.

    python -m auditor.demo examples/with_errors [--no-llm]

Para usar Gemini define GOOGLE_API_KEY en tu entorno (no se guarda en el repo).
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .core.config import gemini_model
from .core.exceptions import FinancialAuditError
from .core.models import FinancialDocument
from .services.audit_service import AuditService
from .services.llm_service import LLMAuditService

ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def _load(folder: Path, stem: str, doc_type: str) -> FinancialDocument:
    for ext, fmt in ((".md", "markdown"), (".csv", "csv")):
        path = folder / f"{stem}{ext}"
        if path.exists():
            return FinancialDocument(content=path.read_text(encoding="utf-8"), doc_type=doc_type, file_format=fmt)
    raise FileNotFoundError(f"No se encontró {stem}.md ni {stem}.csv en {folder}")


def main(argv=None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Audita un P&L y un Balance locales")
    parser.add_argument("folder", type=Path, help="Carpeta con pl.md|csv y balance.md|csv")
    parser.add_argument("--no-llm", action="store_true", help="Solo reglas deterministas")
    args = parser.parse_args(argv)

    llm = LLMAuditService(enabled=False if args.no_llm else None)
    service = AuditService(llm_service=llm)

    try:
        pl = service.document_service.parse_document(_load(args.folder, "pl", "pl"))
        balance = service.document_service.parse_document(_load(args.folder, "balance", "balance"))
    except (FileNotFoundError, FinancialAuditError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    findings, llm_used, llm_error = service.analyze(pl, balance)

    print(f"Periodo: {pl.get('period')}")
    if llm_used:
        print(f"Gemini: activo ({llm.model})")
    elif args.no_llm:
        print("Gemini: desactivado (--no-llm)")
    elif llm_error:
        print(f"Gemini: falló, solo reglas → {llm_error}")
    else:
        print("Gemini: sin credenciales, solo reglas. Define GOOGLE_API_KEY para activarlo.")
    print()

    if not findings:
        print("✅ Sin discrepancias.")
        return 0

    for f in findings:
        origin = "🤖 Gemini" if f.get("source") == "gemini" else "📐 Regla"
        print(f"{ICONS.get(f['severity'], '•')} [{f['severity']}] {f['type']}  ({origin})")
        print(f"   {f['description']}")
        print(f"   → {f.get('fix', '')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
