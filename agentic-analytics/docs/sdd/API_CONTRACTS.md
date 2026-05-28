# Objetivo
Documentar contratos de API com envelope padrão para rastreabilidade uniforme.

## Envelope Padrão
Toda resposta HTTP JSON de sucesso segue:

```json
{
  "trace_id": "uuid",
  "data": {}
}
```

## Contratos por Endpoint
### GET `/`
- `data.service`: nome do serviço.
- `data.version`: versão da API.
- `data.docs`: rota da documentação.

### GET `/api/v1/health`
- `data.status`: `ok` ou `degraded`.
- `data.services`: saúde por dependência (`opensearch`, `ollama`, `postgres`).
- `data.timestamp`: ISO timestamp.

### POST `/api/v1/ask-analytics`
- Request: `{question, workspace_id?, thread_id?, mode?, top_k?, model?}`.
- `data.answer`: resposta textual.
- `data.routed_path`, `data.reasoning_steps`, `data.sql`, `data.sources`, `data.masked_fields`.

### POST `/api/v1/ask-analytics/stream`
- Request: mesmo payload base de pergunta.
- `data.trace_id`: identificador do fluxo SSE.

### POST `/api/v1/search-rules`
- Request: `{query, top_k}`.
- `data.chunks`, `data.sources`, `data.total`.

### GET `/api/v1/traces/{trace_id}`
- `data`: objeto de auditoria retornado do armazenamento.

### `/api/v1/workspaces*`
- `POST /workspaces`: `data` com workspace criado.
- `GET /workspaces`: `data` como lista de workspaces.
- `GET /workspaces/{id}/threads`: `data` como lista de threads.
- `POST /workspaces/{id}/threads`: `data` com thread criada.
- `PUT /workspaces/{id}/agent-md`: `data` com workspace atualizado.
