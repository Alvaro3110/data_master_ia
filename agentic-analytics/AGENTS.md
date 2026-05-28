# Mission

Entregar evolução contínua do `agentic-analytics` com Spec-Driven Development, preservando contratos públicos, segurança e rastreabilidade em cada mudança.

## Responsibilities

### Spec Architect

- Manter `docs/sdd/*` como fonte de verdade para requisitos funcionais e não funcionais.
- Atualizar critérios de aceite e contratos antes de aprovar mudança de comportamento.
- Registrar riscos, dúvidas e decisões em `QUESTIONS.md` e documentos correlatos.

### Software Engineer

- Ler `docs/sdd` antes de codificar.
- Implementar apenas o que estiver coberto por critérios de aceite observáveis.
- Entregar código + teste + atualização de spec no mesmo PR quando houver impacto de contrato.

### Reviewer

- Validar aderência entre código e spec.
- Confirmar que CI de contrato (`validate_sdd`, `test_sdd_*`) está verde.
- Bloquear merge quando houver divergência entre `apps/**` e `docs/sdd/**`.

## Constraints

- Não alterar arquivos fora do escopo da task em andamento.
- Não introduzir requisito novo sem atualização explícita de `docs/sdd`.
- Não usar OpenAI real em PR sem `@pytest.mark.live_openai` e contexto controlado.
- Não aceitar resposta JSON fora do envelope `{trace_id, data}`.

## Workflow

1. Revisar specs relevantes em `docs/sdd` (PRD, SPEC, TASKS, AC).
2. Escrever/ajustar testes para o comportamento esperado.
3. Implementar o mínimo necessário para verde.
4. Executar validações locais (`validate_sdd`, `pytest`, lint).
5. Revisar impacto de contrato e atualizar docs no mesmo PR.
6. Só avançar para próximo slice após fechamento de critérios do slice atual.
