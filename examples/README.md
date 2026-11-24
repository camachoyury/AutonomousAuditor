# Ejemplos

- `with_errors/` — P&L y Balance con errores sembrados a propósito:
  - La utilidad neta del P&L ($400) no coincide con la del Balance ($350). *Lo detecta una regla.*
  - «Ingresos Totales» dice $1,300, pero las partidas suman $1,200, y por eso la utilidad neta no cuadra con ingresos − gastos. *Esto lo debería detectar Gemini.*
- `clean/` — los mismos documentos sin errores (no debería haber hallazgos).

```bash
python -m auditor.demo examples/with_errors
python -m auditor.demo examples/clean
python -m auditor.demo examples/with_errors --no-llm   # solo reglas, sin Gemini
```
