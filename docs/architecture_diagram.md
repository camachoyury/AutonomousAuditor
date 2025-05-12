# Diagrama de Arquitectura - Sistema de Auditoría Financiera

```mermaid
graph TD
    subgraph GitHub
        A[Repositorio Financiero] -->|Push/Trigger| B[Webhook]
    end

    subgraph Auditor
        B -->|Evento| C[GitHub Actions]
        C -->|Inicia| D[Docker Container]
        
        subgraph Agentes
            D --> E[DocumentRetrieverAgent]
            E -->|Docs| F[DocumentParserAgent]
            F -->|Parsed Data| G[ComparisonAgent]
            G -->|Analysis| H[IssueManagerAgent]
        end
        
        H -->|Create/Update| I[GitHub Issue]
    end

    subgraph ADK Core
        J[Modelo Gemini] -->|Prompts| G
        K[Validadores] -->|Rules| G
        L[Parsers] -->|Format| F
    end
```

## Leyenda

- **GitHub**: Repositorio fuente y sistema de eventos
- **Auditor**: Sistema principal de auditoría
- **ADK Core**: Núcleo del sistema de desarrollo autónomo
- **Flechas**: Flujo de datos y eventos
- **Subgraphs**: Agrupación lógica de componentes 