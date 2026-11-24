# Diagrama de Arquitectura - Sistema de Auditoría Financiera

```mermaid
graph TD
    subgraph GitHub
        A[Repo de reportes] -->|push a main| B[Webhook / Action]
    end

    subgraph Auditor
        B -->|POST /webhook/github| C[FastAPI app.py]
        C --> S[AuditService]
        S --> R[GitHubService: recuperar P&L y Balance]
        R --> P[DocumentService: parsear a datos estructurados]
        P --> V[Reglas deterministas]
        V --> L[LLMAuditService: agente ADK + Gemini]
        L --> M[Hallazgos combinados]
        M --> I[GitHubService: crear/actualizar Issue]
    end

    I -->|Issue por periodo| A
    G[Gemini API] <-->|salida estructurada| L
```

## Leyenda

- **Reglas deterministas**: periodo, utilidad neta, ecuación contable y ratios; exactas y sin costo.
- **LLMAuditService**: `LlmAgent` de Google ADK con `output_schema`; revisa totales, clasificación y anomalías que las reglas no cubren. Si falla, la auditoría continúa solo con las reglas.
- **Issue por periodo**: el título es estable (`Auditoría Financiera - <periodo>`), por lo que cada auditoría actualiza el issue abierto en lugar de duplicarlo.
