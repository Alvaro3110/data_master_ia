# Objetivo
Definir contratos dos principais modelos de dados e políticas de tratamento de campos sensíveis.

## Workspace
Campos mínimos:
- `id`: string.
- `nome`: string.
- `user_id`: string.
- `agent_md`: string opcional.
- `criado_em`: timestamp ISO.

## Thread
Campos mínimos:
- `id`: string.
- `workspace_id`: string.
- `titulo`: string.
- `mensagens`: lista de mensagens com `role`, `content`, `metadata`.

## Ask Analytics Response (data)
Campos mínimos:
- `trace_id`, `question`, `answer`, `routed_path`, `reasoning_steps`.
- `sql`, `sql_result`, `sources`, `masked_fields`, `latency_ms`.

## Auditoria de Trace
Campos típicos:
- `trace_id`, `question`, `routed_path`, `sql_final`, `status`, `latency_ms`, `masked_fields`, `created_at`.

## Política de PII
- Campos sensíveis como CPF, e-mail e identificadores de cliente devem ser mascarados antes de resposta final.
- Logs e artefatos não devem persistir valor bruto de PII em texto claro.
