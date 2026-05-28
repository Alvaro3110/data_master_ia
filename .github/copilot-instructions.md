# Copilot Instructions

## Objetivo
Padronizar contribuições assistidas por IA no repositório com foco em SDD, TDD, segurança e rastreabilidade.

## Fluxo Obrigatório
1. Ler `agentic-analytics/docs/sdd/` antes de propor código.
2. Confirmar critérios de aceite em `ACCEPTANCE_CRITERIA.md` e tarefas em `TASKS.md`.
3. Implementar com testes claros e determinísticos.
4. Atualizar specs e contratos quando houver mudança de comportamento.
5. Não concluir tarefa com CI quebrado.

## Regras de Qualidade
- Toda resposta HTTP JSON deve seguir envelope `{trace_id, data}`.
- Consultas SQL geradas por agentes devem passar por validação AST.
- Evitar chamadas LLM reais em testes de PR; usar mocks.
- Priorizar mudanças pequenas e verificáveis por slice vertical.

## Comandos Úteis
- `python agentic-analytics/scripts/validate_sdd.py`
- `python agentic-analytics/scripts/validate_sdd.py --check-diff`
- `pytest -q agentic-analytics/tests/test_sdd_*.py`
- `cd agentic-analytics/apps/backend && uv run pytest tests/unit -m "not live_openai"`
