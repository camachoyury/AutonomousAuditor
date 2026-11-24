# Autonomous Financial Auditor / Auditor Financiero Autónomo

[English](#english) · [Español](#español)

---

## English

### Overview
> **This is an example project, not a product.** It shows how to use **Gemini through Google ADK** to audit financial statements: deterministic rules for what must be exact, an LLM agent with structured output for what rules can't enumerate. No credentials live in this repo — bring your own `GOOGLE_API_KEY`.

An AI-first service that helps finance teams avoid reporting errors. It automatically audits two key documents — the **Quarterly P&L** and the **Balance Sheet** (Markdown or CSV) — stored in a GitHub repository, detects inconsistencies between them, and opens (or updates) a **GitHub Issue** with the findings, their severity and suggested fixes.

Finance teams already keep their reports in Git; the auditor plugs into that workflow so every change is checked the moment it is pushed, instead of being discovered at close time.

### What it does
Given a company's **Quarterly P&L** and **Balance Sheet** (Markdown or CSV), it cross-checks them and reports what doesn't add up — for example:
- the net income in the P&L differs from the one in the Balance Sheet;
- the accounting equation breaks (Assets ≠ Liabilities + Equity);
- a stated total doesn't equal the sum of its line items;
- a ratio (revenue/assets, expenses/revenue) is implausible.

It can run on local files (the demo) or read the documents from a GitHub repository and open one **GitHub Issue per period** with the findings, grouped by severity, each with a suggested fix.

### What it uses
- **Gemini** (Google's LLM, `gemini-2.5-flash` by default) to review the statements for problems that fixed rules can't enumerate.
- **Google ADK** (Agent Development Kit) to define and run the Gemini agent, which answers in a Pydantic-validated JSON schema.
- **Deterministic Python rules** (`Decimal` arithmetic) for everything that must be exact and reproducible.
- **PyGithub** to read the documents and create/update the Issue (optional integration).
- **pandas** to parse CSV files and **FastAPI** for the optional webhook/API.
- **Docker** and **pytest** (Gemini and GitHub are mocked in the tests, so no credentials are needed).

### Try it in 2 minutes (no GitHub needed)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

python -m auditor.demo examples/with_errors --no-llm   # rules only, no key needed
export GOOGLE_API_KEY=<your key>                       # get one at https://aistudio.google.com/apikey
python -m auditor.demo examples/with_errors            # rules + Gemini
```

`examples/with_errors` has two planted mistakes: the net income differs between P&L and Balance (caught by a **rule**), and the stated revenue total doesn't equal the sum of its lines (the kind of thing **Gemini** is there to catch). See [`examples/`](examples/README.md).

### How it works

The full pipeline below reads the documents from a GitHub repo and publishes an Issue; the local demo above runs only steps 3a–3b on local files.

```
 local files / webhook push / manual call
                │
                ▼
   ┌──────────────────────────┐
   │ 1. Retrieve              │  PyGithub: finds the P&L and Balance files
   │    (GitHubService)       │  in the target repo/branch (.md / .csv)
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 2. Parse                 │  Markdown tables / CSV → structured data
   │    (DocumentService)     │  (pandas + Decimal for exact money values)
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 3a. Deterministic rules  │  period, net income, accounting equation,
   │     (AuditService)       │  ratios — exact and free
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 3b. Gemini review        │  ADK LlmAgent with structured output: totals
   │     (LLMAuditService)    │  that don't add up, misclassified items, anomalies
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 4. Report                │  Groups findings by severity; creates or updates
   │    (GitHubService)       │  one GitHub Issue per period
   └──────────────────────────┘
```

1. **Trigger** – A local run (`auditor.demo`), a push to the default branch via a signed GitHub webhook (`POST /webhook/github`, HMAC-SHA256, answered with `202` and audited in the background), or a manual `POST /audit` (protected by `X-API-Key`).
2. **Retrieve** – Using the GitHub API, the auditor lists the files in the branch and picks the P&L (`pl`, `income`, `profit`) and Balance (`balance`, `bs`) documents. The format is taken from the extension (`.md` / `.csv`).
3. **Parse** – Each document becomes line items (revenue, expenses, assets, liabilities, equity) and totals. Amounts are `Decimal`, never floats.
4. **Analyze** – Two layers:
   - **Deterministic rules** (code): both documents cover the **same period**; **net income** in the P&L matches the Balance (tolerance $0.01); the **accounting equation** holds (Assets = Liabilities + Equity); revenue/assets and expenses/revenue ratios are plausible.
   - **Gemini** (through Google ADK): receives the parsed data plus the findings the rules already produced and looks for what rules can't enumerate — totals that don't equal the sum of their lines, net income ≠ revenue − expenses, misclassified or duplicated items, anomalous amounts. It runs at temperature 0 and must answer with a JSON schema (Pydantic `output_schema`), which is validated before use. Each finding is tagged with its origin (📐 rule / 🤖 Gemini).
5. **Report** – Findings are grouped by severity into a single GitHub Issue titled `Auditoría Financiera - <period>` (labels `auditoría`, `finanzas`, `automático`). An open issue for the same period is updated rather than duplicated.

**Graceful degradation:** if there is no `GOOGLE_API_KEY`, or Gemini fails (quota, network, invalid response), the audit still completes with the deterministic rules, and the result reports `llm_used: false` and the `llm_error`.

### Technology stack

| Area | Technology |
|---|---|
| Language | Python 3.11+ (Docker image uses 3.12) |
| Agent framework | [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) 2.x — `LlmAgent` with `output_schema`, `Runner`, `InMemorySessionService` |
| LLM | Google Gemini (`gemini-2.5-flash` by default, configurable with `GEMINI_MODEL`) |
| GitHub integration | [PyGithub](https://pygithub.readthedocs.io/) (files, issues), GitHub webhooks, GitHub Actions |
| Document parsing | pandas (CSV), regex (Markdown tables), `decimal.Decimal` for monetary precision |
| Validation | Pydantic (LLM output schema) |
| API server | FastAPI + Uvicorn (`app.py`) |
| Configuration | Environment variables / `.env` (`python-dotenv`) — see `.env.example` |
| Packaging / runtime | `pyproject.toml` (setuptools), Docker, Docker Compose |
| CI | GitHub Actions (runs the tests; no secrets) |
| Testing | pytest |

### Project structure
```
app.py                    FastAPI server (webhook, /audit, /health)
auditor/
  demo.py                 Local demo: python -m auditor.demo <folder>
  agent.py                GitHub CLI: python -m auditor.agent
  services/
    github_service.py     Retrieve documents, create/update the Issue
    document_service.py   Markdown/CSV → structured data
    audit_service.py      Orchestration + deterministic rules
    llm_service.py        ADK LlmAgent + Gemini (structured output)
  core/                   Config, prompts, models, constants, exceptions
  utils/                  Formatters and validators
  tests/                  Unit tests (GitHub and Gemini are mocked)
examples/                 Sample P&L and Balance (with and without errors)
docs/                     Architecture, rationale and observability
Dockerfile, docker-compose.yml, .github/workflows/
```

### Expected input
The target repository must contain a P&L and a Balance Sheet, e.g.:

```markdown
# P&L
Periodo: Q1 2024

## Ingresos
| Concepto | Monto |
|----------|-------|
| Ventas   | $100,000 |

## Gastos
| Concepto | Monto |
|----------|-------|
| Nómina   | $60,000 |

## Totales
| Concepto | Monto |
|----------|-------|
| Utilidad Neta | $40,000 |
```

CSV files use the columns `Category, Item, Amount`.

### Getting started

```bash
# 1. Install (Python 3.11+)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# 2. Configure
cp .env.example .env     # then fill in GITHUB_TOKEN, GOOGLE_API_KEY, etc.

# 3. Local demo (no GitHub)
python -m auditor.demo examples/with_errors

# 4. Optional GitHub integration — audit a real repo and open an Issue
python -m auditor.agent

# 5. Optional API server (webhook + /audit)
python app.py            # http://127.0.0.1:8000  (uvicorn app:app in Docker, port 8080)
docker compose up --build

# Tests (Gemini and GitHub are mocked: no credentials needed)
pytest
```

| Variable | Purpose |
|---|---|
| `GITHUB_TOKEN` | Read the reports repo and write issues |
| `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_BRANCH` | Repo to audit (CLI / Actions) |
| `GOOGLE_API_KEY` | Enables the Gemini review (optional) |
| `GEMINI_MODEL` | Model name, default `gemini-2.5-flash` |
| `AUDITOR_USE_LLM=false` | Disable Gemini even if a key is set |
| `GITHUB_WEBHOOK_SECRET` | Required for `/webhook/github` (rejected with 401 otherwise) |
| `AUDIT_API_KEY` | Required for `POST /audit` (`X-API-Key` header) |

Credentials are read from your environment or a local `.env` (git-ignored). Nothing in this repo requires GitHub secrets: the only workflow (`tests.yml`) runs the mocked test suite.

### Documentation
- [Architecture Diagram](docs/architecture_diagram.md): visual overview of components and data flow
- [Architecture Rationale](docs/architecture_rationale.md): design decisions, failure modes and scaling
- [Observability](docs/observability.md): logging, metrics, tracing, dashboards and alerting

---

## Español

### Descripción
> **Este es un proyecto de ejemplo, no un producto.** Muestra cómo usar **Gemini con Google ADK** para auditar estados financieros: reglas deterministas para lo que debe ser exacto y un agente LLM con salida estructurada para lo que las reglas no pueden enumerar. El repo no contiene credenciales: usa tu propia `GOOGLE_API_KEY`.

Un servicio *AI-first* que ayuda a los equipos financieros a evitar errores en sus reportes. Audita automáticamente dos documentos clave — el **P&L trimestral** y el **Balance General** (Markdown o CSV) — almacenados en un repositorio de GitHub, detecta inconsistencias entre ellos y crea (o actualiza) un **Issue de GitHub** con los hallazgos, su severidad y las correcciones sugeridas.

Los equipos financieros ya guardan sus reportes en Git; el auditor se integra en ese flujo para que cada cambio se revise en el momento del push, y no al cierre del periodo.

### Qué hace
A partir del **P&L trimestral** y el **Balance General** de una empresa (Markdown o CSV), los cruza y reporta lo que no cuadra — por ejemplo:
- la utilidad neta del P&L difiere de la del Balance;
- se rompe la ecuación contable (Activos ≠ Pasivos + Capital);
- un total declarado no es la suma de sus partidas;
- un ratio (ingresos/activos, gastos/ingresos) es inverosímil.

Puede correr sobre archivos locales (el demo) o leer los documentos de un repositorio de GitHub y abrir **un Issue por periodo** con los hallazgos agrupados por severidad, cada uno con una corrección sugerida.

### Qué usa
- **Gemini** (el LLM de Google, `gemini-2.5-flash` por defecto) para revisar los estados en busca de problemas que las reglas fijas no pueden enumerar.
- **Google ADK** (Agent Development Kit) para definir y ejecutar el agente de Gemini, que responde con un esquema JSON validado por Pydantic.
- **Reglas deterministas en Python** (aritmética con `Decimal`) para todo lo que debe ser exacto y reproducible.
- **PyGithub** para leer los documentos y crear/actualizar el Issue (integración opcional).
- **pandas** para parsear CSV y **FastAPI** para el webhook/API opcional.
- **Docker** y **pytest** (en las pruebas Gemini y GitHub están simulados, así que no hacen falta credenciales).

### Pruébalo en 2 minutos (sin GitHub)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

python -m auditor.demo examples/with_errors --no-llm   # solo reglas, sin clave
export GOOGLE_API_KEY=<tu clave>                       # créala en https://aistudio.google.com/apikey
python -m auditor.demo examples/with_errors            # reglas + Gemini
```

`examples/with_errors` trae dos errores sembrados: la utilidad neta difiere entre P&L y Balance (la detecta una **regla**) y el total de ingresos no es la suma de sus partidas (lo que debería detectar **Gemini**). Ver [`examples/`](examples/README.md).

### Cómo funciona

El flujo completo lee los documentos de un repo de GitHub y publica un Issue; el demo local solo ejecuta los pasos 3a–3b sobre archivos locales.

```
 archivos locales / push por webhook / llamada manual
                │
                ▼
   ┌──────────────────────────┐
   │ 1. Recuperar             │  PyGithub: localiza los archivos de P&L y
   │    (GitHubService)       │  Balance en el repo/rama (.md / .csv)
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 2. Parsear               │  Tablas Markdown / CSV → datos estructurados
   │    (DocumentService)     │  (pandas + Decimal para montos exactos)
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 3a. Reglas deterministas │  periodo, utilidad neta, ecuación contable,
   │     (AuditService)       │  ratios — exactas y sin costo
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 3b. Revisión con Gemini  │  LlmAgent de ADK con salida estructurada: totales
   │     (LLMAuditService)    │  que no suman, partidas mal clasificadas, anomalías
   └────────────┬─────────────┘
                ▼
   ┌──────────────────────────┐
   │ 4. Reportar              │  Agrupa por severidad; crea o actualiza un
   │    (GitHubService)       │  Issue de GitHub por periodo
   └──────────────────────────┘
```

1. **Disparo** – Una ejecución local (`auditor.demo`), un push a la rama principal mediante un webhook firmado (`POST /webhook/github`, HMAC-SHA256; responde `202` y audita en segundo plano), o una llamada manual a `POST /audit` (protegida con `X-API-Key`).
2. **Recuperación** – Con la API de GitHub se listan los archivos de la rama y se eligen el P&L (`pl`, `income`, `profit`) y el Balance (`balance`, `bs`). El formato se deduce de la extensión (`.md` / `.csv`).
3. **Parseo** – Cada documento se convierte en partidas (ingresos, gastos, activos, pasivos, capital) y totales. Los montos son `Decimal`, nunca float.
4. **Análisis** – Dos capas:
   - **Reglas deterministas** (código): ambos documentos cubren el **mismo periodo**; la **utilidad neta** del P&L coincide con la del Balance (tolerancia $0.01); se cumple la **ecuación contable** (Activos = Pasivos + Capital); los ratios ingresos/activos y gastos/ingresos son razonables.
   - **Gemini** (vía Google ADK): recibe los datos parseados y los hallazgos que las reglas ya produjeron, y busca lo que las reglas no pueden enumerar — totales que no igualan la suma de sus partidas, utilidad neta ≠ ingresos − gastos, partidas mal clasificadas o duplicadas, montos anómalos. Corre con temperatura 0 y debe responder con un esquema JSON (`output_schema` de Pydantic) que se valida antes de usarse. Cada hallazgo indica su origen (📐 regla / 🤖 Gemini).
5. **Reporte** – Los hallazgos se agrupan por severidad en un único Issue titulado `Auditoría Financiera - <periodo>` (etiquetas `auditoría`, `finanzas`, `automático`). Si ya hay un issue abierto del mismo periodo, se actualiza en lugar de duplicarse.

**Degradación elegante:** si no hay `GOOGLE_API_KEY`, o Gemini falla (cuota, red, respuesta inválida), la auditoría se completa igualmente con las reglas deterministas y el resultado indica `llm_used: false` y el `llm_error`.

### Tecnologías

| Área | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ (la imagen Docker usa 3.12) |
| Framework de agentes | [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) 2.x — `LlmAgent` con `output_schema`, `Runner`, `InMemorySessionService` |
| LLM | Google Gemini (`gemini-2.5-flash` por defecto, configurable con `GEMINI_MODEL`) |
| Integración con GitHub | [PyGithub](https://pygithub.readthedocs.io/) (archivos, issues), webhooks de GitHub, GitHub Actions |
| Parseo de documentos | pandas (CSV), regex (tablas Markdown), `decimal.Decimal` para precisión monetaria |
| Validación | Pydantic (esquema de salida del LLM) |
| Servidor API | FastAPI + Uvicorn (`app.py`) |
| Configuración | Variables de entorno / `.env` (`python-dotenv`) — ver `.env.example` |
| Empaquetado / ejecución | `pyproject.toml` (setuptools), Docker, Docker Compose |
| CI | GitHub Actions (corre las pruebas; sin secrets) |
| Pruebas | pytest |

### Estructura del proyecto
```
app.py                    Servidor FastAPI (webhook, /audit, /health)
auditor/
  demo.py                 Demo local: python -m auditor.demo <carpeta>
  agent.py                CLI de GitHub: python -m auditor.agent
  services/
    github_service.py     Recuperar documentos, crear/actualizar el Issue
    document_service.py   Markdown/CSV → datos estructurados
    audit_service.py      Orquestación + reglas deterministas
    llm_service.py        LlmAgent de ADK + Gemini (salida estructurada)
  core/                   Config, prompts, modelos, constantes, excepciones
  utils/                  Formateadores y validadores
  tests/                  Pruebas unitarias (GitHub y Gemini simulados)
examples/                 P&L y Balance de muestra (con y sin errores)
docs/                     Arquitectura, justificación y observabilidad
Dockerfile, docker-compose.yml, .github/workflows/
```

### Entrada esperada
El repositorio objetivo debe contener un P&L y un Balance General, por ejemplo:

```markdown
# P&L
Periodo: Q1 2024

## Ingresos
| Concepto | Monto |
|----------|-------|
| Ventas   | $100,000 |

## Gastos
| Concepto | Monto |
|----------|-------|
| Nómina   | $60,000 |

## Totales
| Concepto | Monto |
|----------|-------|
| Utilidad Neta | $40,000 |
```

Los CSV usan las columnas `Category, Item, Amount`.

### Inicio rápido

```bash
# 1. Instalar (Python 3.11+)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# 2. Configurar
cp .env.example .env     # y completar GITHUB_TOKEN, GOOGLE_API_KEY, etc.

# 3. Demo local (sin GitHub)
python -m auditor.demo examples/with_errors

# 4. Integración opcional con GitHub — audita un repo real y abre un Issue
python -m auditor.agent

# 5. Servidor API opcional (webhook + /audit)
python app.py            # http://127.0.0.1:8000  (uvicorn app:app en Docker, puerto 8080)
docker compose up --build

# Pruebas (Gemini y GitHub simulados: no requieren credenciales)
pytest
```

| Variable | Para qué sirve |
|---|---|
| `GITHUB_TOKEN` | Leer el repo de reportes y escribir issues |
| `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_BRANCH` | Repo a auditar (CLI / Actions) |
| `GOOGLE_API_KEY` | Activa la revisión con Gemini (opcional) |
| `GEMINI_MODEL` | Nombre del modelo, por defecto `gemini-2.5-flash` |
| `AUDITOR_USE_LLM=false` | Desactiva Gemini aunque haya API key |
| `GITHUB_WEBHOOK_SECRET` | Obligatorio para `/webhook/github` (si falta, responde 401) |
| `AUDIT_API_KEY` | Obligatorio para `POST /audit` (cabecera `X-API-Key`) |

Las credenciales se leen de tu entorno o de un `.env` local (ignorado por git). Nada en este repo requiere secrets de GitHub: el único workflow (`tests.yml`) corre las pruebas con mocks.

### Documentación
- [Diagrama de Arquitectura](docs/architecture_diagram.md): vista visual de componentes y flujo de datos
- [Racionalización de Arquitectura](docs/architecture_rationale.md): decisiones de diseño, modos de fallo y escalabilidad
- [Observabilidad](docs/observability.md): estrategia de logging, métricas, trazas, dashboards y alertas
