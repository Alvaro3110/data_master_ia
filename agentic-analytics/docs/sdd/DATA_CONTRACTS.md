# Objetivo

Definir os modelos de dados internos e as regras de proteção de dados usados por APIs e agentes.

## Workspace

Campos obrigatórios:

- `id`: string UUID.
- `nome`: string 1..200.
- `user_id`: string.
- `agent_md`: string opcional.
- `criado_em`, `atualizado_em`: ISO-8601.

## Thread

Campos obrigatórios:

- `id`, `workspace_id`, `titulo`, `status`.
- `mensagens`: lista com objetos `{role, content, timestamp, metadata}`.

## Artifact

Campos obrigatórios:

- `id`, `thread_id`, `tipo`, `conteudo`, `metadata`, `criado_em`.
- `tipo` esperado: `markdown | pdf | xlsx | png | json | html`.

## Ask Analytics (data)

Campos mínimos esperados no `data` de `/ask-analytics`:

- `trace_id`, `question`, `answer`, `routed_path`, `reasoning_steps`.
- `retrieval_attempts`, `rewritten_query`, `sources`.
- `sql`, `sql_result`, `masked_fields`, `latency_ms`, `status`.

## Auditoria de Trace

Registro mínimo:

- `trace_id`, `question`, `routed_path`, `sql_final`, `status`, `latency_ms`, `masked_fields`, `created_at`.

Exemplo:

```json
{
  "trace_id": "4de5f05a-85db-4bb2-a30b-5ea73f7f726b",
  "status": "success",
  "routed_path": "analytics",
  "latency_ms": 930,
  "masked_fields": ["cpf"],
  "created_at": "2026-05-28T03:10:22.900Z"
}

```

## Política de PII

- Campos como CPF, e-mail, data de nascimento e identificadores de cliente devem sair mascarados.
- Persistência de auditoria não deve armazenar PII em texto claro.
- Logs de erro devem omitir conteúdo bruto de entrada quando houver dado sensível.
