# Objetivo
Formalizar o problema de negócio e o resultado esperado do `agentic-analytics` com contratos verificáveis por CI, reduzindo deriva arquitetural entre frontend, backend e agentes.

## Contexto de Negócio
A plataforma apoia decisões de pricing, margem, safra e risco de crédito. Respostas incorretas ou não rastreáveis impactam receita, compliance e auditoria. O projeto usa agentes de IA (LangGraph) e, por isso, exige controle explícito de escopo, segurança e observabilidade.

## Público-Alvo
- Analista de pricing e risco que precisa consultar indicadores sem escrever SQL manual.
- Time de engenharia de dados/IA responsável por manter precisão, segurança e latência.
- Time de governança/compliance que exige trilha de auditoria por requisição.

## Casos de Uso Principais
- Perguntar margem por safra e segmento via `POST /api/v1/ask-analytics`.
- Consultar regras de negócio e glossário por busca híbrida (`/api/v1/search-rules`).
- Gerenciar contexto de trabalho com `workspaces`, `threads` e histórico.
- Auditar execução de requisições por `trace_id` em `/api/v1/traces/{trace_id}`.

## Escopo MVP
- Scaffold SDD completo em `docs/sdd/` com critérios testáveis.
- Contrato HTTP canônico `{trace_id, data}` em endpoints JSON.
- Validador SDD + testes (`validate_sdd.py`, `test_sdd_*`) + workflow dedicado.
- Regras mínimas de segurança (SQL guardrails, PII masking, CORS, rate-limit).
- Rastreabilidade com `trace_id` em payload e header.

## Métricas de Sucesso
- CI `sdd-validation` verde em 100% dos PRs com mudança de código.
- Zero endpoint JSON fora do envelope canônico após merge.
- Falhas de contrato detectadas em PR, antes de produção.
- Tempo de investigação de incidente reduzido com correlação por `trace_id`.

## Fora de Escopo
- Tornar Playwright e cobertura global gates obrigatórios nesta etapa.
- Reescrever integralmente a malha de agentes da Fase 3.
- Introduzir novas features de produto sem critério de aceite em `docs/sdd`.
