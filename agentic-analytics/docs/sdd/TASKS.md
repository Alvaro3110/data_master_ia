# Objetivo
Organizar a execução em slices verticais pequenas, auditáveis e vinculadas a critérios de aceite testáveis.

## Vertical Slices
- [ ] VS01: Consolidar estrutura e conteúdo base de `docs/sdd` em PT-BR - Critério de aceite: AC01, AC02, AC03, AC04 com `pytest -q agentic-analytics/tests/test_sdd_structure.py`.
  Objetivo: garantir que os documentos existem, sem placeholders, com seções obrigatórias.
  Artefatos impactados: `docs/sdd/*.md`.
  Verificação: `python agentic-analytics/scripts/validate_sdd.py` retorna `exit 0`.

- [ ] VS02: Tornar critérios de aceite estritamente observáveis (HTTP code, payload e erro) - Critério de aceite: AC05, AC06, AC07, AC08 via revisão em `ACCEPTANCE_CRITERIA.md`.
  Objetivo: remover critérios vagos e descrever sucesso/falha mensuráveis.
  Artefatos impactados: `docs/sdd/ACCEPTANCE_CRITERIA.md`, `docs/sdd/API_CONTRACTS.md`.
  Verificação: itens `ACxx` parseáveis e vinculados aos testes.

- [ ] VS03: Endurecer validador SDD com checks semânticos e placeholders - Critério de aceite: AC09, AC10, AC11 por `python agentic-analytics/scripts/validate_sdd.py`.
  Objetivo: transformar specs em contrato executável com mensagens determinísticas.
  Artefatos impactados: `scripts/validate_sdd.py`, `tests/test_sdd_structure.py`.
  Verificação: falhar ao remover seção obrigatória, placeholder ou formato inválido.

- [ ] VS04: Endurecer gate `--check-diff` para fail-closed - Critério de aceite: AC12, AC13 em `test_sdd_contracts.py`.
  Objetivo: impedir aprovação de PR quando diff não puder ser resolvido em CI.
  Artefatos impactados: `scripts/validate_sdd.py`, `tests/test_sdd_contracts.py`.
  Verificação: simulação de diff indisponível retorna `DIFF_GATE_UNRESOLVED`.

- [ ] VS05: Corrigir infraestrutura de CI backend para `POSTGRES_URL` - Critério de aceite: AC14 em `.github/workflows/ci.yml`.
  Objetivo: alinhar variável de ambiente do workflow ao `config.py` da aplicação.
  Artefatos impactados: `.github/workflows/ci.yml`.
  Verificação: jobs backend usam `POSTGRES_URL` e `TEST_DB_MODE=postgres`.

- [ ] VS06: Padronizar e endurecer política de `trace_id` - Critério de aceite: AC15, AC16, AC17 em testes backend.
  Objetivo: aceitar `X-Trace-ID` apenas se UUID válido; inválido gera novo id.
  Artefatos impactados: `apps/backend/app/main.py`, `apps/backend/tests/**`.
  Verificação: testes validam header válido reutilizado e inválido substituído.

- [ ] VS07: Manter envelope `{trace_id, data}` em todos os endpoints JSON + OpenAPI tipado - Critério de aceite: AC18, AC19, AC20.
  Objetivo: reforçar contrato público e melhorar documentação automática da API.
  Artefatos impactados: `apps/backend/app/api/v1/ask_analytics.py`, `docs/sdd/API_CONTRACTS.md`.
  Verificação: `/ask-analytics` expõe response model de envelope e testes de integração passam.

- [ ] VS08: Ajustar frontend e mocks para consumir apenas `response.data` - Critério de aceite: AC21 em testes frontend.
  Objetivo: remover fallback permissivo do cliente para contrato antigo.
  Artefatos impactados: `apps/frontend/src/components/*.tsx`, `apps/frontend/e2e/chat.spec.ts`.
  Verificação: Jest/Playwright mock usando envelope canônico.

- [ ] VS09: Consolidar políticas de segurança/observabilidade em spec e testes - Critério de aceite: AC22, AC23, AC24.
  Objetivo: explicitar SQL guardrails, PII masking, CORS, rate-limit, métricas e correlação.
  Artefatos impactados: `docs/sdd/SECURITY.md`, `docs/sdd/OBSERVABILITY.md`.
  Verificação: validador detecta ausência de termos críticos.

- [ ] VS10: Fechar governança operacional de agentes e Copilot - Critério de aceite: AC25, AC26, AC27.
  Objetivo: formalizar regras de escopo de edição e leitura obrigatória das specs.
  Artefatos impactados: `AGENTS.md`, `.github/copilot-instructions.md`, `.github/workflows/sdd-validation.yml`.
  Verificação: SDD workflow executa validador, pytest SDD e markdownlint em PR/push.
