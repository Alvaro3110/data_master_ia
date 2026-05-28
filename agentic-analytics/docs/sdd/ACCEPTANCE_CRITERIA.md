# Objetivo

Definir critérios de aceite objetivos para que CI e revisão técnica validem conformidade SDD sem ambiguidade.

## Critérios de Aceite

- AC01: Todos os arquivos obrigatórios de `docs/sdd/` existem e são não vazios.
- AC02: Cada documento obrigatório contém H1 e snippets mandatórios definidos em `validate_sdd.py`.
- AC03: Não há marcadores de pendência ou texto fictício proibido nos arquivos SDD.
- AC04: `TASKS.md` possui itens no formato `- [ ] VSxx: ... - Critério de aceite: ...`.
- AC05: `ACCEPTANCE_CRITERIA.md` possui itens no formato `- ACxx: ...`.
- AC06: `QUESTIONS.md` possui itens no formato `- Qxx: ...`.
- AC07: `ARCHITECTURE.md` contém ao menos um bloco Mermaid.
- AC08: `API_CONTRACTS.md` contém no mínimo 2 blocos `json` com `trace_id` e `data`.
- AC09: `TEST_PLAN.md` contém política explícita de `pytest`.
- AC10: `TEST_PLAN.md` contém política explícita de `playwright`.
- AC11: `TEST_PLAN.md` contém política explícita de `live_openai` para chamadas reais.
- AC12: `validate_sdd.py --check-diff` falha quando `apps/**` muda sem `docs/sdd/**`.
- AC13: `validate_sdd.py --check-diff` falha com `DIFF_GATE_UNRESOLVED` quando diff não é determinável em CI.
- AC14: `.github/workflows/ci.yml` usa `POSTGRES_URL` compatível com `config.py` e não `DATABASE_URL`.
- AC15: `GET /` retorna HTTP 200 com envelope `{trace_id, data}`.
- AC16: Se `X-Trace-ID` enviado for UUID válido, backend reutiliza o valor em header e payload.
- AC17: Se `X-Trace-ID` enviado for inválido, backend gera novo UUID e não propaga o valor inválido.
- AC18: `GET /api/v1/health` retorna HTTP 200 com `data.status` e `trace_id`.
- AC19: `POST /api/v1/ask-analytics` retorna HTTP 200 em envelope com `data.answer` e `data.routed_path`.
- AC20: `/api/v1/workspaces*`, `/api/v1/traces/{trace_id}` e `/api/v1/search-rules` retornam envelope padronizado.
- AC21: Frontend (`WorkspaceSidebar`, `ChatPanel`) consome apenas `response.data`; mock E2E segue envelope canônico.
- AC22: `SECURITY.md` descreve guardrails SQL via `sqlglot`, PII masking, CORS restrito e rate-limit.
- AC23: `OBSERVABILITY.md` descreve `trace_id`, logs estruturados e métricas de latência/erro.
- AC24: SSE `GET /ask-analytics/stream/{trace_id}` mantém stream e evento `done` com `trace_id`.
- AC25: `AGENTS.md` contém `Mission`, `Responsibilities`, `Constraints`, `Workflow`.
- AC26: `AGENTS.md` explicita regra: "Não alterar arquivos fora do escopo da task".
- AC27: `.github/copilot-instructions.md` exige leitura de `docs/sdd` antes de codar e atualização de specs no mesmo PR.
