# Objetivo
Definir estratégia de testes para desenvolvimento orientado a especificação, com foco em segurança, contrato e previsibilidade.

## Estratégia de Testes
- Backend unitário e integração com `pytest`.
- Frontend unitário com Jest/RTL e E2E opcional com Playwright.
- Testes SDD em `agentic-analytics/tests/test_sdd_*.py` para governança de documentação.

## Política de Mocks
- Testes de PR não podem chamar OpenAI real.
- Integrações com LLM devem usar mocks determinísticos ou fallback local (Ollama).
- Chamadas reais só são permitidas em testes marcados com `@pytest.mark.live_openai` em ambientes controlados.

## Critérios de Aprovação
- `python agentic-analytics/scripts/validate_sdd.py` com exit code 0.
- `pytest -q agentic-analytics/tests/test_sdd_*.py` passando.
- Suítes backend/frontend críticas sem regressão de contrato.
- Workflow `sdd-validation` verde em PR.

## Evidências Esperadas
- Log de execução do validador SDD.
- Saída do pytest da suíte SDD.
- Registro de atualização dos contratos em `docs/sdd` no mesmo PR de mudanças de código.
