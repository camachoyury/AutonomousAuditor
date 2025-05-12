# Autonomous Financial Auditor / Auditor Financiero Autónomo

## English

### Overview
This project is an AI-First SaaS platform designed to help finance teams avoid reporting errors. It automatically audits two key financial documents (Quarterly P&L and Balance Sheet, in Markdown or CSV) from a GitHub repository, detects inconsistencies, and creates or updates a GitHub Issue with findings and suggested fixes.

### Table of Contents
- [Architecture Diagram](docs/architecture_diagram.md)
- [Architecture Rationale](docs/architecture_rationale.md)
- [Observability](docs/observability.md)

### Key Features
- Retrieves and parses financial documents on every push to main or manual trigger
- Compares line items (revenues, COGS, assets, liabilities, totals, etc.)
- Detects inconsistencies (e.g., Net Income in P&L ≠ change in retained earnings)
- Summarizes discrepancies and proposes fixes in a single GitHub Issue

### Documentation
- [Architecture Diagram](docs/architecture_diagram.md): Visual overview of system components and data flow
- [Architecture Rationale](docs/architecture_rationale.md): Explanation of design decisions, failure modes, and scaling
- [Observability](docs/observability.md): Logging, metrics, tracing, dashboards, and alerting strategy

---

## Español

### Descripción
Este proyecto es una plataforma SaaS impulsada por IA para ayudar a los equipos financieros a evitar errores en reportes. Audita automáticamente dos documentos clave (P&L trimestral y Balance General, en Markdown o CSV) desde un repositorio de GitHub, detecta inconsistencias y crea o actualiza un Issue con hallazgos y sugerencias de corrección.

### Tabla de Contenidos
- [Diagrama de Arquitectura](docs/architecture_diagram.md)
- [Racionalización de Arquitectura](docs/architecture_rationale.md)
- [Observabilidad](docs/observability.md)

### Funcionalidades Clave
- Recupera y parsea documentos financieros en cada push a main o trigger manual
- Compara partidas clave (ingresos, COGS, activos, pasivos, totales, etc.)
- Detecta inconsistencias (ej: utilidad neta en P&L ≠ cambio en ganancias retenidas)
- Resume discrepancias y propone correcciones en un solo Issue de GitHub

### Documentación
- [Diagrama de Arquitectura](docs/architecture_diagram.md): Vista visual de componentes y flujo de datos
- [Racionalización de Arquitectura](docs/architecture_rationale.md): Decisiones de diseño, modos de fallo y escalabilidad
- [Observabilidad](docs/observability.md): Estrategia de logging, métricas, trazas, dashboards y alertas 