# Observabilidad del Sistema de Auditoría Financiera

## 1. Logging

### Logs Estructurados
```python
{
    "timestamp": "ISO8601",
    "level": "INFO|WARNING|ERROR",
    "agent": "DocumentRetrieverAgent|DocumentParserAgent|ComparisonAgent|IssueManagerAgent",
    "action": "retrieve|parse|compare|create_issue",
    "status": "success|failure",
    "duration_ms": 123,
    "metadata": {
        "repo": "camachoyury/financial-reports",
        "branch": "main",
        "files": ["pl.md", "balance.md"],
        "error": "optional_error_message"
    }
}
```

### Niveles de Logging
- **DEBUG**: Detalles de procesamiento interno
- **INFO**: Operaciones normales
- **WARNING**: Situaciones inesperadas pero manejables
- **ERROR**: Fallos que requieren atención
- **CRITICAL**: Fallos que afectan el servicio

## 2. Métricas

### Métricas de Agentes
```python
# DocumentRetrieverAgent
document_retrieval_duration_seconds
document_retrieval_success_total
document_retrieval_failure_total

# DocumentParserAgent
document_parsing_duration_seconds
document_parsing_success_total
document_parsing_failure_total

# ComparisonAgent
comparison_duration_seconds
discrepancies_found_total
validation_success_total

# IssueManagerAgent
issue_creation_duration_seconds
issue_creation_success_total
issue_creation_failure_total
```

### Métricas de Sistema
```python
# Docker
container_cpu_usage_percent
container_memory_usage_bytes
container_network_io_bytes

# GitHub API
github_api_rate_limit_remaining
github_api_request_duration_seconds
github_api_error_total
```

## 3. Trazas Distribuidas

### Spans por Operación
```python
# Document Retrieval
span_retrieval = {
    "name": "document_retrieval",
    "attributes": {
        "repo": "camachoyury/financial-reports",
        "branch": "main",
        "files": ["pl.md", "balance.md"]
    }
}

# Document Parsing
span_parsing = {
    "name": "document_parsing",
    "attributes": {
        "file_type": "markdown",
        "file_size": 1234,
        "parsed_items": 56
    }
}

# Comparison
span_comparison = {
    "name": "financial_comparison",
    "attributes": {
        "discrepancies": 3,
        "validation_rules": 5,
        "severity": "high"
    }
}
```

## 4. Dashboards

### Dashboard Principal
- **Estado del Sistema**
  - Uptime
  - Tasa de errores
  - Latencia promedio

- **Métricas de Agentes**
  - Tiempo de procesamiento
  - Tasa de éxito
  - Discrepancias encontradas

- **Métricas de GitHub**
  - Rate limit
  - Tiempo de respuesta API
  - Errores de API

### Dashboard de Negocio
- **Eficiencia**
  - Tiempo ahorrado
  - Errores detectados
  - Calidad de reportes

- **Tendencias**
  - Discrepancias por tipo
  - Tiempo de resolución
  - Mejoras en calidad

## 5. Alertas

### Alertas Críticas
```yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 1%
    duration: 5m
    severity: critical

  - name: api_rate_limit
    condition: rate_limit_remaining < 100
    duration: 1m
    severity: warning

  - name: processing_timeout
    condition: processing_duration > 30s
    duration: 1m
    severity: critical
```

### Alertas de Negocio
```yaml
alerts:
  - name: high_discrepancy_rate
    condition: discrepancies_per_doc > 5
    duration: 1h
    severity: warning

  - name: low_detection_rate
    condition: detection_rate < 90%
    duration: 1d
    severity: warning
```

## 6. Implementación

### Configuración de Logging
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Configuración de Métricas
```python
from prometheus_client import Counter, Histogram, Gauge

# Métricas de Agentes
document_retrieval_duration = Histogram(
    'document_retrieval_duration_seconds',
    'Time spent retrieving documents'
)

discrepancies_found = Counter(
    'discrepancies_found_total',
    'Number of discrepancies found',
    ['severity']
)
```

### Configuración de Trazas
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

tracer = trace.get_tracer(__name__)
```

## 7. Herramientas Recomendadas

- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Métricas**: Prometheus + Grafana
- **Trazas**: Jaeger
- **Alertas**: AlertManager
- **Dashboards**: Grafana 