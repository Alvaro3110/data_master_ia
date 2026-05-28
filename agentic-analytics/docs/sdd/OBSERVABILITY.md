# Objetivo
Definir rastreabilidade ponta a ponta para diagnóstico rápido, auditoria de decisões e medição de qualidade operacional.

## Trace ID
- Middleware injeta `trace_id` em toda request.
- `trace_id` retorna no header `X-Trace-ID` e no envelope JSON.
- Se cliente enviar `X-Trace-ID` inválido, servidor gera novo UUID.
- SSE deve concluir com evento `done` contendo `trace_id`.

## Logs Estruturados
- Logs em JSON com `timestamp`, `level`, `trace_id`, `endpoint`, `status_code`.
- Em caso de erro, registrar causa técnica e contexto mínimo sem expor PII.
- Eventos críticos: bloqueio SQL, falha de dependência, fallback de provedor, timeout.

## Métricas
- Latência p50/p95 de `/api/v1/health` e `/api/v1/ask-analytics`.
- Taxa de erro por endpoint (4xx e 5xx).
- Taxa de bloqueio de segurança (SQL validator, guardrail, rate-limit).
- Throughput de eventos SSE por `trace_id` para análise de streaming.

## Alertas Operacionais
- Alerta para aumento súbito de erro (`5xx`) ou latência acima do SLO.
- Alerta de dependência degradada (Postgres/Redis/OpenSearch).
- Alerta de regressão de contrato detectada por validações SDD em CI.
