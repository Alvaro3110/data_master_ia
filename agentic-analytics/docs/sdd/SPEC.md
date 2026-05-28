# Objetivo
Especificar a arquitetura técnica executável do `agentic-analytics` e os contratos que orientam implementação, revisão e CI.

## Stack Técnica
- Frontend: Next.js + React + TypeScript.
- Backend: FastAPI + Pydantic + SQLAlchemy.
- Orquestração: LangGraph com nós de guardrail, roteamento e especialistas.
- Banco transacional: PostgreSQL (principal) com fallback técnico controlado para SQLite em testes locais.
- Banco analítico: DuckDB para cenários locais e trilhas de auditoria.
- Busca semântica: OpenSearch (RAG híbrido).
- Cache/stream: Redis para eventos SSE e replay.
- Segurança SQL: `sqlglot` para parsing AST e bloqueio de comandos perigosos.

## Arquitetura de Referência
Fluxo padrão: `Frontend -> FastAPI -> LangGraph -> (DuckDB/Postgres/OpenSearch/Redis) -> resposta envelope {trace_id, data}`.

## Padrões Arquiteturais
- Contrato primeiro: toda mudança em `apps/**` com impacto funcional deve atualizar `docs/sdd/**`.
- Envelope único: respostas HTTP JSON sempre incluem `trace_id` e `data`.
- SSE separado: `GET /ask-analytics/stream/{trace_id}` mantém streaming, com evento `done` contendo `trace_id`.
- Falha explícita: validações de diff e contrato falham em CI quando não determinísticas.

## Fluxos de Dados Críticos
- Pergunta analítica: validação de escopo -> roteamento -> SQL/RAG -> mascaramento PII -> persistência de auditoria.
- Workspaces: criação/listagem de contexto -> threads -> mensagens com metadata e `trace_id`.
- Traces: consulta de auditoria por id para suporte a debugging e compliance.

## Dependências e Restrições
- Testes de PR não podem chamar OpenAI real.
- Uso de OpenAI real somente em testes marcados `@pytest.mark.live_openai` fora do fluxo padrão.
- Em CI, `TEST_DB_MODE=postgres`; localmente, `TEST_DB_MODE=auto` permite fallback SQLite.
- CORS com origens explícitas; sem wildcard com credenciais.

## Restrições Não Funcionais
- Latência observável por endpoint crítico (`/health`, `/ask-analytics`).
- Logs estruturados com `trace_id` e status.
- Reprodutibilidade: qualquer falha de contrato deve ser detectável por `validate_sdd.py` + `pytest`.
