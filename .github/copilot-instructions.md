# Copilot Instructions

## Objetivo

Padronizar contribuições assistidas por IA com foco em SDD, TDD e contrato público estável.

## Fluxo Obrigatório

1. Ler `agentic-analytics/docs/sdd/` antes de escrever código.
2. Confirmar `TASKS.md` e `ACCEPTANCE_CRITERIA.md` para mapear o slice ativo.
3. Implementar mudanças pequenas e testáveis; evitar escopo extra.
4. Atualizar `docs/sdd/**` no mesmo PR quando `apps/**` mudar comportamento.
5. Encerrar somente com validações locais e CI verdes.

## Regras de Qualidade

- Toda resposta HTTP JSON usa envelope `{trace_id, data}`.
- `X-Trace-ID` só é aceito se UUID válido.
- SQL gerado por agentes deve passar por validação AST (`sqlglot`).
- Em PR, evitar chamadas reais de LLM; usar mocks/fallback.
- Não alterar arquivos fora do escopo sem necessidade explícita.

## Regras de Teste

- `pytest` para backend e governança SDD.
- `playwright` para E2E com mocks de envelope e SSE.
- Testes `@pytest.mark.live_openai` fora do gate padrão de PR.

## Comandos Úteis

- `python agentic-analytics/scripts/validate_sdd.py`
- `python agentic-analytics/scripts/validate_sdd.py --check-diff`
- `pytest -q agentic-analytics/tests/test_sdd_*.py`
- `cd agentic-analytics/apps/backend && uv run pytest tests/unit -m "not live_openai"`
