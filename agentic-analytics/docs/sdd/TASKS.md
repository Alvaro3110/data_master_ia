# Objetivo
Detalhar as fatias verticais de implementação com critérios de aceite observáveis.

## Vertical Slices
- [ ] VS01: Criar estrutura base de SDD em `docs/sdd` com documentos obrigatórios - Critério de aceite: AC01, AC02, teste `agentic-analytics/tests/test_sdd_structure.py`.
- [ ] VS02: Escrever conteúdo inicial dos specs com contexto real do projeto - Critério de aceite: AC03, AC04, AC05, teste `agentic-analytics/tests/test_sdd_contracts.py`.
- [ ] VS03: Implementar validador `scripts/validate_sdd.py` com checagens de existência, seções e placeholders - Critério de aceite: AC06, AC07, AC08, execução `python agentic-analytics/scripts/validate_sdd.py`.
- [ ] VS04: Adicionar gate `--check-diff` para exigir atualização de SDD quando `apps/**` mudar - Critério de aceite: AC09, AC10, teste `agentic-analytics/tests/test_sdd_contracts.py`.
- [ ] VS05: Criar workflow dedicado `.github/workflows/sdd-validation.yml` com markdownlint e pytest - Critério de aceite: AC11, AC12, revisão de workflow em PR.
- [ ] VS06: Padronizar envelope `{trace_id, data}` nas respostas HTTP JSON do backend - Critério de aceite: AC13, AC14, AC15, testes backend de integração e unitários.
- [ ] VS07: Ajustar frontend para parsing de `response.data` em workspaces e inicialização de stream - Critério de aceite: AC16, teste `apps/frontend/src/__tests__/WorkspaceSidebar.test.tsx` e `ChatPanel.test.tsx`.
- [ ] VS08: Atualizar contratos e políticas em `API_CONTRACTS.md`, `DATA_CONTRACTS.md`, `SECURITY.md`, `OBSERVABILITY.md` - Critério de aceite: AC17, AC18, validação de headings e conteúdo.
- [ ] VS09: Consolidar governança de agentes em `AGENTS.md` e `.github/copilot-instructions.md` - Critério de aceite: AC19, AC20, validação de conteúdo pelo script SDD.
