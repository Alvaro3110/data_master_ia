# Objetivo

Definir contratos HTTP públicos de forma canônica e testável, com envelope único para todas as respostas JSON.

## Envelope Padrão

Toda resposta HTTP JSON segue este contrato:

```json
{
  "trace_id": "7d2d4ce2-2d24-4d3a-9f7b-a74d8ea2d894",
  "data": {}
}

```

## Contratos de Sucesso

### GET `/`

- Status: `200`
- Body: `data.service`, `data.version`, `data.docs`, `data.health`.

```json
{
  "trace_id": "f77d7f18-0d41-4b0e-b7d4-7bf6d176f39e",
  "data": {
    "service": "Agentic Analytics API",
    "version": "0.1.0",
    "docs": "/api/docs",
    "health": "/api/v1/health"
  }
}

```

### GET `/api/v1/health`

- Status: `200`
- Body: `data.status`, `data.timestamp`, `data.services`.

### POST `/api/v1/ask-analytics`

- Status: `200`
- Request mínimo: `{ "question": "..." }`
- Body: `data.answer`, `data.routed_path`, `data.reasoning_steps`, `data.sql`, `data.sources`, `data.masked_fields`, `data.latency_ms`.

### POST `/api/v1/ask-analytics/stream`

- Status: `200`
- Body: `data.trace_id`.

### GET `/api/v1/ask-analytics/stream/{trace_id}`

- Tipo: `text/event-stream`.
- Evento `done`: inclui `trace_id` no JSON do evento.

### POST `/api/v1/search-rules`

- Status: `200`
- Request: `{ "query": "...", "top_k": 3 }`
- Body: `data.query`, `data.chunks`, `data.sources`, `data.total`.

### GET `/api/v1/traces/{trace_id}`

- Status: `200` quando encontrado, `404` quando ausente.
- Body: `data` com registro de auditoria.

### `/api/v1/workspaces*`

- `POST /workspaces` -> `201`, `data` com workspace criado.
- `GET /workspaces` -> `200`, `data` lista de workspaces.
- `GET /workspaces/{id}/threads` -> `200`, `data` lista de threads.
- `POST /workspaces/{id}/threads` -> `201`, `data` thread criada.
- `PUT /workspaces/{id}/agent-md` -> `200`, `data` workspace atualizado.

## Contratos de Erro

Erros também seguem envelope com `trace_id`:

```json
{
  "trace_id": "6d8e7f2f-5d23-41c7-aab1-6cdf9f1f0a10",
  "data": {
    "detail": "Workspace 'abc' não encontrado."
  }
}

```

## Política de Compatibilidade

- Qualquer alteração de payload exige update em `docs/sdd` e testes de contrato.
- Mudanças breaking devem ser registradas em `QUESTIONS.md`/planejamento de versionamento.
