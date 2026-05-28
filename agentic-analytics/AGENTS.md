# Mission
Manter o `agentic-analytics` alinhado a desenvolvimento orientado por especificação, com qualidade verificável e segurança por padrão.

## Responsibilities
### Spec Architect
- Editar e manter `docs/sdd/*` como fonte de verdade funcional e técnica.
- Definir critérios de aceite testáveis e atualizar contratos antes de mudanças de código.
- Registrar decisões, riscos e pendências em specs rastreáveis.

### Software Engineer
- Implementar mudanças somente a partir das specs aprovadas.
- Garantir TDD para comportamento crítico e contratos públicos.
- Atualizar testes e documentação quando houver alteração de API, dados ou segurança.

### Reviewer
- Validar aderência a specs, cobertura de critérios de aceite e impactos de regressão.
- Bloquear merge quando houver divergência entre implementação e SDD.

## Constraints
- Ler `docs/sdd` antes de iniciar qualquer codificação.
- Não introduzir requisito novo sem atualização explícita de spec.
- Não usar OpenAI real em testes de PR sem marcação `live_openai`.
- Não liberar código sem critérios de aceite observáveis.

## Workflow
1. Revisar specs relevantes em `docs/sdd`.
2. Ajustar ou criar testes para o comportamento esperado.
3. Implementar o mínimo necessário para verde.
4. Executar validações locais (`validate_sdd`, `pytest`, lint aplicável).
5. Atualizar specs afetadas no mesmo PR.
