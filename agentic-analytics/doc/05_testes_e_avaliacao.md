# Testes, TDD e Avaliação Contínua

Para viabilizar as implementações complexas do Agentic Analytics, tudo foi estruturado sob o prisma do **Test-Driven Development (TDD)** e testabilidade corporativa.

## 1. Testes Estáticos e Unitários (Backend & Frontend)
- **Backend:** Temos uma suíte que supera **120 testes**. Todo agente (`data_agent`, `risk_agent`) foi validado individualmente *mockando* o LLM para responder rapidamente a intenções sem precisar gastar recursos, viabilizando o CI/CD.
- **Integração:** `test_swarm_routing.py` assegura que um Supervisor não cometa erros triviais de envio (e garante compatibilidade com as rotas que o React aguarda receber na resposta, como os vetores `routed_path`).
- **Frontend (RTL/Jest):** A UI não é caótica. Com 45 testes automatizados, validamos comportamentos como exibição adequada de Markdown, interações de Sidebar (Workspaces) e persistência em interface.

## 2. A Fase 5 e as Avaliações de LLM-as-a-judge (Bulk Evals)
Sistemas com IA generativa sofrem com instabilidades. Uma resposta que ontem estava perfeita amanhã pode vir com formatações que quebram o parser do cliente, ou o LLM pode alucinar se o prompt for discretamente alterado.
Para isso introduzimos uma Camada de Evals (Avaliação Contínua):

### `evaluate_relevance`
- Um sub-LLM (Juiz) lê friamente a pergunta que o usuário fez e compara com a resposta gerada.
- Retorna um JSON estrito contendo uma pontuação e uma justificativa.
- Se o Ollama estiver *offline* no container de testes, cai para um **Fallback Heurístico** que utiliza contagem ponderada (Overlap) ignorando pontuação.

### `evaluate_sql_accuracy`
- Avalia programaticamente se o SQL construído no Node final tenta forçar *bypasses* sobre o banco, inspecionando menções a nomes sensíveis (`passwords`, `secrets`) e confirmando o match das tabelas previstas (`pricing_data`).

### O Tool: `scripts/evaluate_langsmith.py`
Para garantir a qualidade na esteira, adicionamos um utilitário de *Bulk Evaluation*. 
- Ele varre um *dataset* em lote, envia cada requisição individualmente ao Backend, analisa o score emitido pelos *Evaluators* e apresenta no console um grid rico via lib `rich`.
- Salva ao final os *KPIs* (`eval_report.json`), o que futuramente acoplaremos nativamente a SDKs do LangSmith ou Langfuse para a governança plena de Observabilidade de IA.
