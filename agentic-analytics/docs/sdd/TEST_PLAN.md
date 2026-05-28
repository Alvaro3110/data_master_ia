# Objetivo

Definir estratégia de teste orientada a contrato para garantir que mudanças de código não quebrem especificações SDD, segurança e rastreabilidade.

## Estratégia de Testes

- `pytest` para testes unitários, integração e governança SDD.
- `playwright` para E2E frontend com mocks controlados de API/SSE.
- Jest/RTL para comportamento de componentes críticos (`WorkspaceSidebar`, `ChatPanel`).
- Separação de escopo: contrato e segurança são validados em PR; testes pesados podem rodar em jobs dedicados.

## Política de Mocks

- Em PR, é proibido chamar OpenAI real nas suítes padrão.
- Fluxos de LLM devem usar mocks determinísticos ou fallback local (Ollama).
- Chamadas reais só em testes explicitamente marcados com `@pytest.mark.live_openai`.
- Testes `live_openai` ficam fora do gate padrão de PR e rodam manualmente ou em janela noturna.

## Política de Infra de Banco

- CI backend usa `POSTGRES_URL` com serviço PostgreSQL disponível.
- Ambiente local usa `TEST_DB_MODE=auto` para fallback SQLite quando Postgres não estiver disponível.
- `TEST_DB_MODE=postgres` falha de forma explícita se conexão não for possível.

## Critérios de Aprovação

- `python agentic-analytics/scripts/validate_sdd.py` retorna `exit 0`.
- `python agentic-analytics/scripts/validate_sdd.py --check-diff` retorna `exit 0` em mudanças válidas.
- `pytest -q agentic-analytics/tests/test_sdd_*.py` passa integralmente.
- Testes de contrato backend para envelope e `trace_id` passam.
- Testes frontend alvo de parsing de envelope passam.

## Evidências Esperadas

- Log do validador SDD e da suíte `test_sdd_*` anexado ao PR.
- Saída dos testes backend/frontend alterados na entrega.
- Referências cruzadas entre mudanças em `apps/**` e updates em `docs/sdd/**`.
