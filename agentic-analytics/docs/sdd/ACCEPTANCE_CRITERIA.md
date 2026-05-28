# Objetivo
Definir critérios de aceite objetivos e testáveis para validação automática da disciplina SDD.

## Critérios de Aceite
- AC01: Todos os arquivos obrigatórios de `docs/sdd` existem.
- AC02: Cada arquivo obrigatório possui conteúdo não vazio e cabeçalhos Markdown válidos.
- AC03: `PRD.md` inclui objetivo, contexto de negócio, público-alvo, casos de uso e escopo.
- AC04: `SPEC.md` inclui stack, arquitetura, fluxos e restrições não funcionais.
- AC05: `TASKS.md` usa o padrão `- [ ] VSxx: ... - Critério de aceite: ...`.
- AC06: `ACCEPTANCE_CRITERIA.md` usa o padrão `- ACxx: ...`.
- AC07: `ARCHITECTURE.md` contém ao menos um bloco Mermaid válido.
- AC08: Não há placeholders proibidos (marcadores de pendência ou textos genéricos) nos arquivos SDD.
- AC09: `validate_sdd.py --check-diff` falha quando há mudança em `agentic-analytics/apps/**` sem mudança em `agentic-analytics/docs/sdd/**`.
- AC10: `validate_sdd.py --check-diff` passa quando há mudança em `apps/**` e em `docs/sdd/**` no mesmo diff.
- AC11: Workflow `sdd-validation.yml` roda em `push` para `main` e `pull_request`.
- AC12: Workflow executa validador SDD, pytest de SDD e markdownlint.
- AC13: Endpoint `/api/v1/health` responde com `{trace_id, data}` e `data.status`.
- AC14: Endpoint `/api/v1/ask-analytics` responde com `{trace_id, data}` e `data.answer`.
- AC15: Endpoints de workspaces e traces retornam envelope com `trace_id`.
- AC16: Frontend consome `response.data` para listas de workspaces, threads e trace inicial de stream.
- AC17: `API_CONTRACTS.md` documenta envelope padrão em todos endpoints HTTP JSON.
- AC18: `TEST_PLAN.md` formaliza política de `@pytest.mark.live_openai` para chamadas reais.
- AC19: `AGENTS.md` contém seções `Mission`, `Responsibilities`, `Constraints`, `Workflow`.
- AC20: `.github/copilot-instructions.md` exige leitura de `docs/sdd` antes de codar.
