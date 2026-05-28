# Objetivo

Consolidar políticas de segurança aplicáveis a SQL, dados sensíveis, rede e consumo de LLM com regras auditáveis.

## Validador SQL

- Toda query gerada por agente deve passar por parsing AST com `sqlglot`.
- Bloquear obrigatoriamente: `DROP`, `ALTER`, `TRUNCATE`, `DELETE`, multi-statement e funções perigosas.
- `UPDATE`/`DELETE` só permitidos com políticas explícitas (fora do escopo atual do runtime).
- Queries sem limite ou full scan devem ser restringidas por guardrail técnico.

## Guardrails de Prompt e Execução

- Perguntas fora de escopo devem ser bloqueadas pelo guardrail de domínio.
- Fluxos programáticos (PTC/sandbox) devem registrar tentativa e resultado com `trace_id`.

## Mascaramento de PII

- Aplicar masking antes de resposta e antes de persistência de auditoria.
- Exemplos de campos sensíveis: `cpf`, `email`, `data_nascimento`, `cliente_id`.
- Política recomendada: padrões mascarados (`***`) para saída de API e logs.

## CORS

- `allow_origins` deve ser lista explícita de domínios confiáveis.
- Não usar `allow_origins=["*"]` junto com credenciais.
- `allow_headers` e `allow_methods` devem ser revisados periodicamente.

## Rate-limit e Custos

- Aplicar rate-limit por cliente/chave para evitar abuso (`429` em excesso).
- Restringir uso de modelos pagos em PR e ambientes não produtivos.
- Monitorar orçamento por endpoint crítico (`ask-analytics`) com alertas de consumo.

## Segredos e Configuração

- Segredos apenas por variáveis de ambiente (`OPENAI_API_KEY`, etc.).
- Nunca versionar tokens/chaves no repositório.
- CI deve validar ausência de chamadas live fora de `live_openai`.
