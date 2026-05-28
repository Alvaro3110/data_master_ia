# Objetivo
Descrever a visão técnica executável do `agentic-analytics` para orientar implementações e revisões automatizadas.

## Stack Técnica
- Frontend: Next.js + React + TypeScript.
- Backend: FastAPI + Python 3.12.
- Orquestração: LangGraph e agentes especialistas.
- Dados: DuckDB e PostgreSQL.
- Busca semântica: OpenSearch.
- Cache e streaming: Redis.
- Segurança de SQL: `sqlglot` para parsing AST.

## Arquitetura de Referência
Fluxo principal: Frontend -> FastAPI -> LangGraph (guardrail, roteamento, agentes) -> camadas de dados e busca -> resposta auditável.

## Padrões Arquiteturais
- Separação explícita entre contratos (`docs/sdd`) e implementação (`apps`).
- TDD para features críticas de segurança e contratos.
- Política de fallback controlado para provedores LLM.
- Não executar chamadas OpenAI reais em testes de PR.

## Fluxos de Dados Críticos
- `ask-analytics`: pergunta, roteamento, geração SQL/RAG, mascaramento e auditoria.
- `workspaces`: persistência de contexto conversacional.
- `traces`: rastreabilidade de execução.

## Restrições Não Funcionais
- Toda resposta HTTP JSON deve conter `trace_id` e `data`.
- Logs devem suportar correlação por `trace_id`.
- Políticas de PII e SQL seguro são obrigatórias em runtime.
