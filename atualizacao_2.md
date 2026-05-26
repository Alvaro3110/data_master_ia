# Resumo Executivo

Este relatório avalia o repositório **Data Master IA** (do projeto *Agentic Analytics*) em comparação ao projeto **LangAlpha**, focando na preparação para a Fase 3. Constatamos que a **Fase 2.5** (validação e hardening) expôs vários gaps em funcionalidade, testes e segurança. Embora a base exista (FastAPI, Next.js, LangGraph/agents, Docker, etc.), vários componentes críticos ainda estão inacabados ou frágeis. Antes de prosseguir para a Fase 3, é essencial reforçar **TDD em todas as camadas**, implementar testes automatizados (unitários, integração e e2e), configurar mocks de LLM e definir políticas de CI rigorosas (usar ambiente OpenAI simulado em PRs, testes “live_openai” apenas em nightly). Este relatório detalha o estado atual, lacunas, casos de teste TDD recomendados, prioridades e passos de correção. 

Brevemente, destacamos: o *backend* FastAPI tem endpoints básicos (e.g. `/health`, `/api/v1/ask-analytics`), mas precisa validação de entrada (bloqueio de SQL perigoso, mascaramento de dados sensíveis) e testes de unidade. O *frontend* Next.js renderiza o chat, mas deve suportar SSE/streaming robusto e reconexão automática; requer testes e2e com Playwright (capturando fluxo de eventos e gráficos). A arquitetura de agentes usa LangGraph, mas falta um **Supervisor** formal para orquestrar sub-agentes (como LangAlpha faz com diversos especialistas【41†L335-L343】【41†L368-L376】). A persistência de contexto (PostgreSQL/Redis para *Workspaces* e estado de SSE) não parece completa. O sandbox PTC está apenas como subprocesso local; deveríamos suportar provedor seguro (e.g. [Daytona](#) ou outra solução Cloud) para isolar código gerado. A integração LLM deve usar *OpenAI API oficial* por padrão (custos por token, limites de taxa【22†L58-L66】【17†L736-L744】) e usar Ollama local só como fallback. Devem-se distinguir testes simulados (mock OpenAI) de testes reais (marcados como “live_openai” e rodados fora do CI). Em síntese, antes de liberar a Fase 3 devemos completar a Fase 2.5, garantindo estabilidade e segurança: todos os testes críticos verdes, sem skips ativos, políticas de CI aprovadas e documentação de testes. 

A seguir detalhamos cada área, com status atual, lacunas, casos de teste TDD recomendados (arquivo, nome e asserção), prioridade (P0=alta, P1= média, P2=baixa), passos de implementação, comandos de execução e sugestões de diagramas mermaid.

## Estrutura do Projeto

- **Status atual:** Estrutura em monorepo com pastas separadas para backend (FastAPI), frontend (Next.js) e talvez agentes. Possui `Dockerfile`/`docker-compose.yml`, mas convém revisar se todos os serviços (e.g. Postgres, Redis, OpenSearch, Ollama) estão definidos corretamente. Há notas de modelos de dados (ex.: `app/models/workspace.py` planejado) que precisam ser implementados.
- **Lacunas:**  
  - Ausência ou incompletude de modelos para *Workspace/Thread* em banco de dados (persistência de sessão).  
  - Possíveis erros de importação ou configurações de ambiente (ex.: conflito `OLLAMA_HOST` vs `OLLAMA_BASE_URL`).  
  - `sqlglot` ou outras libs não listadas em dependências (verificar `pyproject.toml`/`requirements.txt`).  
  - CORS indiscriminado (`allow_origins=["*"]` com credenciais) é inseguro.
- **Testes TDD Sugeridos (exemplos):**  
  | Arquivo/Teste                            | Asserção                                                               | Prioridade |  
  |:----------------------------------------|:-----------------------------------------------------------------------|:---------:|  
  | `tests/api/test_health.py`<br>`test_health_status`           | Retorna HTTP 200 {"status":"OK"}.                                     | P0        |  
  | `tests/backend/test_env_vars.py`<br>`test_ollama_host_env`    | Erro se `OLLAMA_HOST`/`BASE_URL` mal configurados.                   | P1        |  
  | `tests/backend/test_cors.py`<br>`test_cors_origins`           | Origem não whitelist * não permitida, só domínios esperados.        | P1        |
- **Passos de implementação:**  
  1. Criar/ajustar `workspace.py` (modelos SQLAlchemy) e migrar dados de sessão para Postgres.  
  2. Revisar `pyproject.toml` para incluir libs usadas (`sqlglot`, `openai-responses`, etc.).  
  3. Corrigir variáveis de ambiente: escolher padrão (e.g. `OPENAI_API_KEY` ou `OLLAMA_BASE_URL`).  
  4. Restringir CORS a origens seguras (rodar testes com origens específicas).  
  5. Validar com `docker-compose up --build` que todos os serviços iniciam; criar Dockerfiles faltantes (e.g. para web ou API).
- **Diagramas Mermaid recomendados:**  
  - **Diagrama de Arquitetura:** mostrar serviços: Next.js, FastAPI, LangGraph/Agentes, Postgres, Redis, OpenSearch, Sandbox.  
  - **Diagrama de Fluxo SSE:** cliente -> API SSE -> EventSourceResponse -> front-end.  
  - **Diagrama de PTC:** ilustra ciclo: Agente → gera código → Sandbox (Daytona/E2B) → resultado (JSON/imagem) → UI.  

## Docker e Docker Compose

- **Status atual:** Deve existir `docker-compose.yml` orquestrando serviços (API, web, DBs, etc.). Pode haver referências a imagens ou Dockerfiles não presentes.  
- **Lacunas:**  
  - Verificar se `docker-compose.yml` lista todos os serviços (FastAPI, Next.js, Postgres, Redis, Ollama, OpenSearch, LangChainKit).  
  - Confirmação de versões de Node/Python compatíveis nos Dockerfiles.  
  - Ambiente local requer `docker-compose up`; sem deploy manual.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                          | Asserção                                                         | Prioridade |  
  |:--------------------------------------|:-----------------------------------------------------------------|:---------:|  
  | `tests/integration/test_docker.py`<br>`test_compose_services_up` | `docker compose up --build` executa sem erros (status 0).         | P2        |  
- **Passos de implementação:**  
  1. Atualizar `docker-compose.yml`: mapear variáveis `.env`, volume para persistência (Postgres, Redis), expor portas.  
  2. Criar Dockerfile para cada serviço faltante (frontend e backend se necessário).  
  3. Testar localmente: `docker-compose up --build`.  
- **Comando para reproduzir:**  
  ```bash
  docker-compose up --build
  ```  

## Backend FastAPI e Endpoints

- **Status atual:** O backend FastAPI provê endpoints REST principais, tipicamente `/api/v1/health` e `/api/v1/ask-analytics`. De acordo com o plano, o endpoint `/ask-analytics` executa o fluxo completo de busca de dados e LLM.  
- **Lacunas:**  
  - Necessita implementar *health check* retornando status.  
  - Entrada `/ask-analytics`: validar e sanitizar a pergunta do usuário (bloquear SQL malicioso, injeção de scripts, etc.).  
  - Geração de `trace_id`: cada resposta deve incluir um identificador único para rastreio (atualmente ausente).  
  - Máscara de PII: campos sensíveis (ex: `cliente_id`) devem ser mascarados antes do log ou resposta.  
  - Validar erros: todos os endpoints devem capturar exceções (500/400) adequadamente.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                                   | Asserção                                                                                     | Prioridade |  
  |:-----------------------------------------------|:--------------------------------------------------------------------------------------------|:---------:|  
  | `tests/api/test_health.py`<br>`test_health`                       | GET `/health` retorna 200 e `{"status":"OK"}`.                                               | P0        |  
  | `tests/api/test_ask_analytics.py`<br>`test_ask_returns_sql`      | POST `/ask-analytics` com pergunta analítica devolve JSON com campo `sql` contendo `SELECT`. | P0        |  
  | `tests/backend/test_sql_injection.py`<br>`test_block_delete_drop`| Ao enviar pergunta contendo `DROP TABLE`, o endpoint rejeita (400) sem executar SQL.         | P0        |  
  | `tests/backend/test_masking.py`<br>`test_pii_masking`            | Pergunta com `cliente_id` retorna resposta com `cliente_id` mascarado (e.g. `XXXX`).         | P1        |  
  | `tests/backend/test_trace_id.py`<br>`test_trace_id_present`      | Cada resposta tem campo `trace_id` não-nulo.                                                  | P0        |  
- **Passos de implementação:**  
  1. Criar endpoint `@app.get("/health")` retornando JSON estático (e.g. `{"status":"OK"}`)【38†L212-L220】.  
  2. Em `/ask-analytics`, usar **Text-to-SQL** com **sqlglot** para validar sintaxe. Antes de executar, checar palavras-chave perigosas (`DELETE`, `DROP`, etc.) em lista negra.  
  3. Ao montar resposta, incluir `trace_id = uuid4()` e repassar via header ou JSON.  
  4. Identificar campos sensíveis e aplicar mascaramento (ex.: substituir `cliente_id=1234` por `cliente_id=XXXX`).  
  5. Escrever testes unitários (usando `pytest`) para cada caso acima; usar fixtures do FastAPI [`TestClient`](https://fastapi.tiangolo.com/advanced/testing/) para chamadas HTTP.  
  6. Documentar endpoints (OpenAPI) conforme padrão.
- **Comando para rodar testes:**  
  ```bash
  pytest -v
  ```  

## Frontend Next.js e SSE

- **Status atual:** O frontend (Next.js) implementa chat interativo. Deve consumir o backend via SSE (Server-Sent Events) para exibir respostas parciais *chunked*. Pode existir componente `ChatPanel` e `ArtifactViewer`.  
- **Lacunas:**  
  - **Reconexão SSE:** Implementar reconexão automática com `last-event-id` se a conexão cair.  
  - **Renderização de streams:** O chat deve exibir *streaming* de resposta (pensamento do agente) em tempo real.  
  - **Renderização de artefatos:** Quando o PTC gerar artefatos (gráficos, tabelas), usar um componente tipo `<ArtifactViewer>` para exibir (HTML, base64 ou path).  
  - **Roteamento dinâmico:** Painel lateral (`<WorkspaceSidebar>`) para múltiplas sessões de pesquisa.  
  - **Testes front-end:** Ainda não implementados ou insuficientes.
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                                  | Asserção                                                                                   | Prioridade |  
  |:----------------------------------------------|:------------------------------------------------------------------------------------------|:---------:|  
  | `tests/frontend/test_rendering.js`<br>`test_homepage_loads`           | Página inicial ("/") carrega sem erros (status 200) e contém título do projeto.            | P1        |  
  | `tests/frontend/test_chat_flow.js`<br>`test_streaming_response`      | Usuário envia pergunta; Playwright intercepta SSE e verifica que chat exibe tokens em fluxo. | P0        |  
  | `tests/frontend/test_artifact_viewer.js`<br>`test_graph_rendering`   | Ao receber imagem/HTML do sandbox, `<ArtifactViewer>` renderiza sem falha.                 | P1        |  
  | `tests/frontend/test_workspace_reconnect.js`<br>`test_reconnect_sse` | Desconectando manualmente, reconnecta usando `last-event-id` e recupera mensagens.         | P1        |  
- **Passos de implementação:**  
  1. Usar `EventSource` para conexão SSE no frontend; configurar reconexão com `EventSource.lastEventId`.  
  2. No React, armazenar fluxo de mensagens em estado e renderizar incrementalmente.  
  3. Implementar `<ArtifactViewer>` capaz de distinguir texto, HTML, base64, JSON.  
  4. Adicionar rotas e componente de sidebar de workspaces (usar `useState` ou contexto para sessões).  
  5. Escrever testes e2e com **Playwright**. Segundo a [documentação do FastAPI](#) e artigos de teste real-time, Playwright permite interceptar SSE e assertar mudanças na UI【38†L208-L212】. Usar `pnpm exec playwright test` para rodar.
- **Comando para reproduzir e2e:**  
  ```bash
  pnpm test           # testes unitários frontend
  pnpm exec playwright test  # testes e2e
  ```  

## LangGraph / Agentes (Supervisor vs Especialistas)

- **Status atual:** O sistema baseia-se no LangGraph (semelhante a LangAlpha) para orquestrar agentes. Pelo plano, há agentes **DataAgent** (text2sql + extração) e **RiskAgent** (análise estatística). Falta um supervisor claro ou “grafo monolítico” está em uso.  
- **Lacunas:**  
  - **Falta de Supervisor/Planner:** Diferente de LangAlpha, não há agente central planejando tarefas passo a passo【41†L335-L343】. Isso limita a flexibilidade para múltiplos objetivos (ex: conciliar dados e risco).  
  - **Especialistas limitados:** Apenas dois agentes; LangAlpha tem vários (`researcher`, `market`, `coder`, etc.)【41†L342-L350】.  
  - **DSL de tarefas:** LangGraph sugere definir fluxo via DSL, mas não parece implementado. Falta formalizar “perguntas conceituais” (RAG) e “analíticas” (SQL) separadamente.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                                    | Asserção                                                                                         | Prioridade |  
  |:------------------------------------------------|:------------------------------------------------------------------------------------------------|:---------:|  
  | `tests/agents/test_supervisor.py`<br>`test_invoke_experts`    | Dada pergunta complexa, o Supervisor chama simultaneamente DataAgent e RiskAgent (mockados).     | P1        |  
  | `tests/agents/test_specialist_output.py`<br>`test_data_and_risk_output` | DataAgent e RiskAgent produzem respostas coerentes (mock LLM), verificando interação.             | P1        |  
  | `tests/agents/test_skills_usage.py`<br>`test_skill_prompting`       | Agentes usam corretamente prompts definidos em `skills/` via MCP.                                | P2        |  
- **Passos de implementação:**  
  1. Criar um **SupervisorAgent** (pode ser em `app/agent/graph.py`) que recebe a pergunta e replica a estrutura do LangGraph: 1) usar um `planner` interno para decompor tarefas; 2) usar `pydantic`/LangChain templates para prompts.  
  2. Configurar agentes especialistas em arquivos separados (`specialists/data_agent.py`, `risk_agent.py`), cada um com prompt e lógica distinta.  
  3. Integrar via LangGraph: o supervisor envia subtasks para cada especialista (concorrente) e aguarda respostas.  
  4. Testar em modo isolado: mocks de LLM (por exemplo, sobrecarregando `openai.ChatCompletion.create` para retornar conteúdo fixo)【36†L329-L337】.  
- **Referências (LangAlpha):** LangAlpha implementa uma arquitetura parecida: um `supervisor` delega a múltiplos agentes (`researcher`, `market`, etc.) em paralelo【41†L335-L343】【41†L342-L349】. O supervisor revisa e solicita iterações, finalizando com um `reporter` formatador【41†L359-L364】【41†L368-L376】.

## Persistência (PostgreSQL, Redis, DuckDB)

- **Status atual:** Mencionou-se PostgreSQL e Redis no plano (para sessões e SSE). Provavelmente DuckDB é usado no DataAgent para consultas locais. No entanto, a documentação sugere que **Workspace/Thread** ainda vive na memória.  
- **Lacunas:**  
  - **Workspaces voláteis:** Se o servidor reinicia, o histórico/pesquisa atual se perde. Precisa armazenar no Postgres (conforme rascunho de `app/models/workspace.py`).  
  - **Conexões SSE:** Redis deve ser usado para guardar buffers de eventos e permitir múltiplos consumidores. Se não implementado, SSE falha em reconectar.  
  - **DuckDB:** Se usado em container, definir volume persistente ou reconstrução de dados a partir do Postgres.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                               | Asserção                                                                                              | Prioridade |  
  |:-------------------------------------------|:-----------------------------------------------------------------------------------------------------|:---------:|  
  | `tests/integration/test_workspace.py`<br>`test_workspace_persistence`  | Criada sessão, reiniciado servidor, workspace recarregado do DB (mesmo histórico).                    | P1        |  
  | `tests/integration/test_redis_sse.py`<br>`test_sse_after_reconnect`   | Simula reconexão SSE: Redis contém eventos anteriores e cliente recebe mensagens perdidas.             | P2        |  
- **Passos de implementação:**  
  1. Implementar modelos SQLAlchemy: `Workspace` (id, nome, metadados) e `Thread` (perguntas/respostas vinculadas).  
  2. Criar endpoints CRUD para Workspaces (`GET/POST/PUT/DELETE /api/v1/workspaces`) e armazenar na tabela.  
  3. No backend, injetar pool do Redis para enfileirar/deque SSE: cada evento enviado ao cliente é gravado no Redis por `trace_id`. Use [fastapi_utils.Depepends](#) para disponibilizar Redis na API.  
  4. Adaptar o frontend para recuperar eventos pendentes via Reconnect (com `last-event-id`), lendo do Redis.  
  5. Testar end-to-end: crie workspace, pergunte, reinicie serviço, verifique contexto intacto (use comandos Docker para reiniciar container).
- **Diagrama Mermaid sugerido:** Fluxo de sessão: Cliente → Next.js → API/Redis/DB → dados carregados e eventos SSE armazenados e reaplicados.  

## Sandboxing (Daytona vs E2B)

- **Status atual:** No plano, o sandbox PTC está sendo tratado localmente (provavelmente usando `subprocess` para executar código Python). Isso **não** isola processos nem protege o sistema.  
- **Lacunas:**  
  - **Isolamento insuficiente:** Execução local expõe variáveis de ambiente e rede interna. Conforme best practice, o código gerado pelo LLM deve rodar em sandbox (e.g. [Daytona](#) ou similar) para evitar segurança/privacidade comprometidas.  
  - **Persistência de sandbox:** Ao contrário de Daytona (que tem “snapshots” e persistência)【8†L110-L119】, o atual sandbox local não mantém estado entre execuções (importante se o agente continuar sessão).  
  - **Cloud E2B:** O LangAlpha menciona Daytona vs E2B. E2B (provavelmente “Everything2Build” Cloud) pode ser usado se não houver restrição de cloud, facilitando hackathons. Avaliar o trade-off: E2B é fácil, mas Daytona é mais profissional e seguro.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                               | Asserção                                                                                                                | Prioridade |  
  |:-------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|:---------:|  
  | `tests/integration/test_sandbox.py`<br>`test_code_execution`  | Executa código simples via sandbox (mock Daytona) e retorna resultado esperado (ex: print).                              | P1        |  
  | `tests/security/test_sandbox_isolation.py`<br>`test_no_env_access` | Sandbox não acessa variáveis privadas (ex.: `print(os.getenv())` retorna vazio).                                         | P0        |  
  | `tests/security/test_sandbox_network.py`<br>`test_no_network_access`| Tenta comando malicioso (e.g. `requests.get('http://internal')`) e deve falhar ou bloquear (time-out sem acesso).        | P0        |  
- **Passos de implementação:**  
  1. Abstrair atual executador de código em `SandboxExecutor` (pasta `agent/tools`), de forma que possa usar tanto subprocess local quanto API do Daytona/E2B.  
  2. Integrar o SDK do Daytona (via pip) ou API da solução Cloud; implementar exemplo básico do [Daytona guide](https://daytona.io/docs) para criar sandbox e executar código (ao menos in-memory).  
  3. Garantir que o sandbox limpe ambiente por execução e não tenha acesso a `os.environ` ou rede.  
  4. Testar isolamento: insira código malicioso nos testes acima e assegure que sandbox previne vazamento de dados ou acesso externo.  
  5. Configurar fallback para casos de erro: p.ex. se Daytona indisponível, executar localmente (menos seguro) apenas em ambiente de debug.  
- **Referências:** Daytona oferece “full composable computers” com kernel e filesystem dedicados【8†L110-L118】, com criação de sandbox em <90ms【8†L115-L123】 e snapshots persistentes【8†L121-L125】. Esses recursos garantem ambientes consistentes para agentes.  
- **Diagrama:** Fluxo PTC: Agente → gera código → Daytona API: cria sandbox → sandbox.exec(código) → retorna stdout+arquivos → agente envia ao frontend.  

## Integração LLM (OpenAI vs Ollama)

- **Status atual:** O plano sugere usar **OpenAI oficial** para geração de prompts, com Ollama local como fallback. Atualmente podem estar usando Ollama (self-hosted) como default.  
- **Lacunas:**  
  - **Configuração de provider LLM:** Implementar `LLMProvider` que escolha modelo/serviço: primeiro tenta OpenAI (requer `OPENAI_API_KEY`), se falha ou não configurado, cai em Ollama (local).  
  - **Chaves/segredos:** Garantir que CI não exponha chave real; usar variáveis de ambiente seguras.  
  - **Testes mock:** Em ambiente de teste (CI), chamar a LLM real deve ser proibido (custo e lentidão). Devem existir mocks determinísticos da API OpenAI.  
  - **Taxas e custo:** Monitorar uso de tokens. Tarifas atuais (2026) são listadas na [página oficial](#) da OpenAI (ex.: GPT-5.4 — US$2.50/1M tokens entrada, US$15.00/1M tokens saída【22†L58-L66】). Rate limits variam por modelo【17†L775-L784】.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                                 | Asserção                                                                                                     | Prioridade |  
  |:---------------------------------------------|:------------------------------------------------------------------------------------------------------------|:---------:|  
  | `tests/integration/test_llm_integration.py`<br>`test_openai_fallback`  | Simular falha OpenAI (chave inválida): `LLMProvider` usa Ollama e retorna resposta plausível.           | P1        |  
  | `tests/unit/test_openai_mock.py`<br>`test_mock_openai_api`  | Com `@openai_responses.mock()`, a chamada `openai.ChatCompletion.create` retorna valor fixo predefinido【36†L329-L337】. | P0        |  
  | `tests/integration/test_live_openai.py`<br>`test_real_openai_only_if_enabled` | Marcador `live_openai`: só executa se API key real presente. Em CI normal, ignora (skip).                  | P2        |  
- **Passos de implementação:**  
  1. Criar classe `LLMProvider` que encapsule chamadas a OpenAI Python SDK ou endpoint REST, e caso `openai.OpenAIError` ou falta de credenciais, altera para Ollama (via HTTP).  
  2. Configurar modelo padrão (e.g. “gpt-4o”). Permitir parâmetro de modelo via config.  
  3. No CI, usar [pytest-marker] `@pytest.mark.live_openai` para testes que autorizam OpenAI real. Outras rotinas devem usar o plugin [openai-responses](#) para simular【36†L329-L337】.  
  4. Adicionar política de retry/backoff: em caso de rate-limit, aguardar 1s e tentar novamente (OpenAI recomenda isso【17†L736-L744】).  
  5. Monitorar tokens via callback (usar `token_callback` do SDK) e abortar se ultrapassar limite configurado.  
- **Referências:** OpenAI impõe limites de requisições (RPM, TPM, etc.) para evitar abuso【17†L736-L744】. Custos por token devem ser controlados (ex.: pontos de corte ou modelos menores em dev). O plugin `openai-responses` oferece mocking automático em pytest【36†L329-L337】.

## PTC (Programmatic Tool Calling / Execução de Código)

- **Status atual:** O fluxo PTC permite que a LLM gere código Python para análise (e.g. gráficos). Provavelmente o backend envia perguntas e recebe código-fonte, depois executa.  
- **Lacunas:**  
  - **Formatação de saída:** O agente deve rotular código e artefatos na resposta (por exemplo, usando JSON com campos `code`, `image`, `html`). O frontend renderiza de forma adequada.  
  - **Armazenamento de artefatos:** Resultados (imagens, dados CSV) precisam ser retornados ao cliente. Implementar upload de arquivos gerados no sandbox e acesso via URL temporária.  
  - **Testes de resiliência:** Se o código gerado falhar, não quebrar todo fluxo; capturar erros e incluir mensagens amigáveis.  
- **Testes TDD Sugeridos:**  
  | Arquivo/Teste                              | Asserção                                                                                         | Prioridade |  
  |:------------------------------------------|:-------------------------------------------------------------------------------------------------|:---------:|  
  | `tests/integration/test_ptc_flow.py`<br>`test_code_exec_to_artifact` | Pergunta analítica (gerar gráfico). Verifica que o navegador exibe uma tag `<img>` ou `<canvas>`. | P0        |  
  | `tests/security/test_ptc_file_cleanup.py`<br>`test_no_temp_files_left` | Após execução, não ficam scripts ou credenciais no container.                                     | P1        |  
- **Passos de implementação:**  
  1. Definir protocolo de resposta do agente: o LLM deve usar sintaxe MCP/JSON (ex: `{"code": "...", "files": [{"name":"chart.png"}]}`).  
  2. No `SandboxExecutor`, habilitar upload de arquivos criados (ponteiro a bucket ou base64).  
  3. No frontend, `<ArtifactViewer>` lê o JSON do SSE e renderiza: imagens base64 em `<img>`, tabelas em `<table>`, HTML direto, etc.  
  4. Testar fluxos e2e: enviar pergunta que gere código de plotagem (`matplotlib` etc.), confirmar que a imagem aparece no chat.  

## Testes (Unitários, Integração, E2E Playwright)

- **Status atual:** Há alguns testes de unidade (ex.: `test_guardrail.py`) e possivelmente placeholders. Faltam testes automatizados abrangentes em cada camada. A Fase 2.5 foca em **TDD completo**: escrever testes primeiro, ver falhas, implementar e passar.  
- **Lacunas:**  
  - Muitos componentes sem testes correspondentes (veja quadro abaixo).  
  - Ausência de diferenciação entre testes que usam a LLM real e mocks (tudo no mesmo grupo).  
  - Testes e2e com Playwright não implementados.  
  - Pipelines de teste (pytest e `pnpm test`) devem ser acionados no CI.  
- **Casos de Teste TDD Recomendados (indicados acima)**: saúde da API, fluxo `/ask-analytics`, streaming SSE, SQL perigoso, trace_id, PII, sandbox, LLM fallback.  
- **Tabela de Checklists:**  

  | **Funcional (✔)**                                                   | **Quebrado/Em Falta (✘)**                                                      |
  |:--------------------------------------------------------------------|:-------------------------------------------------------------------------------|
  | *Endpoint* `/api/v1/health` retornando OK                            | Testes automatizados de unidades/integridade ausentes ou incompletos          |
  | Login/UX básico do chat Next.js                                      | SSE streaming parcial (sem reconexão robusta)                                  |
  | DataAgent básico (Text-to-SQL) produce SQL                           | Plano de agentes não usa Supervisor formal (sem “planner” dinamicamente)       |
  | Docker Compose inicia alguns serviços (provavelmente)                | Falta persistência de Workspaces (dados voláteis)                             |
  | Uso de LangGraph para agentes (mecanismo base existente)            | Sandbox padrão local sem isolamento; PTC incompleto                            |
  | CORS habilitado (porém muito amplo, **precisa restringir**)          | Nenhuma política de mocking no CI (OpenAI chamado diretamente)                 |

- **Plano de Correção por Prioridade:**  

  | Prioridade | Item                                                           | Ação                                                                 |
  |:----------:|:----------------------------------------------------------------|:---------------------------------------------------------------------|
  | **P0**     | Health endpoint; SQL injection; trace_id; LLM mocks em CI      | Escrever testes falhando; implementar health, validações e mocks.     |
  | **P0**     | /ask-analytics funcionando completo (SQL seguro, RAG separado)  | Testar fluxo analítico; corrigir Text2SQL e RAG logic.               |
  | **P0**     | Mascaramento PII; sandbox básico seguro                        | Adicionar filtros PII; configurar sandbox (Daytona/E2B) e testá-lo.  |
  | **P1**     | SSE streaming e reconexão                                    | Testar manualmente e com Playwright; ajustar EventSource e reconexão.|
  | **P1**     | LLMProvider com fallback; OpenAI vs Ollama                    | Implementar provedor, classes de configuração, lógica de fallback.   |
  | **P1**     | Persistência de Workspace e sessão via Redis/Postgres         | Criar modelos DB; migrar sessões; testes de reinício de servidor.     |
  | **P2**     | Testes e2e adicionais (Playwright); cobertura de frontend     | Escrever cenários Playwright: login, chat completo, visualização.     |
  | **P2**     | Documentação & CI setup (GitHub Actions, etc.)                | Configurar pipeline: rodar `pytest`, `pnpm test`, `playwright test`.  |

- **Comando único para suíte de testes completa:**  
  ```bash
  docker-compose up --build -d && pytest -v && pnpm test && pnpm exec playwright test
  ```
  Este comando sobe toda stack, executa testes Python e testes front-end. Critérios de aceitação: todos passam (nenhum skip), a Fase 3 pode ser iniciada somente com tudo verde.

## Políticas de CI e Mock vs Real

- **Status atual:** Sem CI definido explicitamente. É necessário um pipeline que:
  1. **Bloqueie PRs** se testes fundamentais falharem.  
  2. **Use mocks LLM** em PRs para custo/consistência (e.g. usando [openai-responses](#))【36†L329-L337】.  
  3. **Marque testes “live_openai”**: estes só rodam quando variável `OPENAI_API_KEY` estiver definida (ex.: nightly build), e são ignorados via `pytest.mark.skip` em CI normal.  
- **Recomendações:**  
  - Em GitHub Actions, defina jobs separados: `unit-tests`, `integration-tests`, `playwright-e2e`.  
  - Em `unit-tests`, usar plugin para mockar todas as chamadas OpenAI【36†L329-L337】.  
  - Em `integration-tests`, usar SQLite/ducky para Text2SQL local e mock de sandbox.  
  - Não commitar chaves de API reais; use *secrets* no CI apenas para jobs agendados.  
  - Falha em qualquer teste P0 deve impedir merge e Fase 3.  

## Workflow TDD

- Seguir rigorosamente o ciclo **Red-Green-Refactor**【46†L53-L60】 em cada camada:
  1. Escrever teste que **falha** (por falta de código ou funcionalidade).  
  2. Executar `pytest`/`pnpm test` e confirmar falha.  
  3. Implementar o mínimo de código para satisfazer o teste.  
  4. Rodar de novo até passar.  
  5. Refatorar mantendo os testes verdes.  
- Exemplos de práticas: escrever testes pequenos e isolados, usar nomeação descritiva, testar casos esperados e inesperados【46†L53-L60】【46†L155-L163】.  
- Fluxo TDD garante cobertura e estabilidade: cada melhoria ou correção inicia com teste novo.  

## Segurança (SQLi, PII, CORS)

- **SQL Injection:** Aplicar **validação de consulta** antes de executar. Usar `sqlglot` para parse seguro ou consultas parametrizadas. Rejeitar queries contendo comandos destrutivos (`DROP`, `DELETE`) ou corpo malicioso. Testes unitários devem enviar payloads tipo `"; DROP TABLE clientes;--"` e garantir HTTP 400.  
- **Mascaramento de Dados Sensíveis:** Quaisquer campos confidenciais (CPF, cliente_id, endereços) devem ser ofuscados. Exemplo: o campo `cliente_id` substituído por “XXXX” na resposta ou logs【36†L329-L337】.  
- **CORS:** Não usar `["*"]` em produção. Deverá listar apenas origens autorizadas (domínios da UI). Teste envio de requisição de origem não whitelist e esperar rejeição CORS.  
- **Sandbox Seguro:** Como acima, impedir escape do sandbox (isolamento, sem acesso ambiente/rede).  
- **Outras diretrizes:** Seguir OWASP TOP 10 – especialmente validação de input e handling de erros sem vazar stack trace.  

## Custos e Rate-Limits (OpenAI)

- **Custos:** A OpenAI cobra por token gerado/consumido. Exemplos de preços (a partir de 2026): GPT-5.4 – US$2.50 por 1M tokens de input, US$15.00 por 1M de output【22†L58-L66】. Deve-se monitorar a fatura e oferecer opções mais baratas (modelos menores ou Batch API) se necessário.  
- **Rate-Limits:** API impõe limites (requests/minuto, tokens/minuto por modelo)【17†L736-L744】. Usar retry exponencial ao detectar 429.  
- **Políticas:** Definir limites de uso no código (timeout + fallback a um modelo menor se atingir quota). Exibir avisos de uso próximo ao limite (até de forma proativa).  
- **Testes faltantes:** incluir verificação de tratamento de `RateLimitError`, com mock enviando 429 e assertando nova tentativa/backoff.  

## Diferenciação Testes Reais vs Simulados

- **Simulados (Mocks):** Devem ser padrão no CI. Usar ferramentas como [openai-responses](#) para criar mocks automáticos de chamadas OpenAI【36†L329-L337】. Os dados de entrada e saída do LLM nos testes devem ser determinísticos.  
- **Reais:** Apenas em cenários controlados (e.g. teste marcado `live_openai`, ou pipeline nightly). Esses testes confirmam que a integração com o endpoint oficial funciona, mas **não** podem rodar em todo PR (custo e flakiness).  
- **Critérios de Bloqueio:** Nenhum PR deve falhar em testes “mocked”. Se um teste `live_openai` falhar (Timeout, ou limite de tokens), deve apenas *avisar*, não bloquear o merge (já que não é executado no PR).  

## Critérios de Liberação da Fase 3

Para avançar à Fase 3, exigimos:

- Todos os testes unitários e de integração marcados P0/P1 passando (suíte completa verde).  
- Testes end-to-end (Playwright) P0/P1 executados em pipeline, com sucesso.  
- Zero skips silenciosos: qualquer teste crítico desabilitado deve ser consertado ou explicitamente comentado com planos de manutenção.  
- Códigos de funcionalidade (TDD) estão implementados conforme testes (princípio Red-Green).  
- Documentação de testes e instruções de CI atualizadas (como rodar, marcar testes live, coverage).  
- Política de segurança aplicada (verificação de SQLi, máscaras).  
- Guidelines de custo e LLM definidas.  

Somente com estes critérios satisfeitos o projeto estará **estável e previsível** para prosseguir com a próxima fase de desenvolvimento (adicionar novas features). 

**Referências:** o método TDD e melhores práticas são bem descritos por Leonard de Assis【46†L53-L60】. O uso de SSE com FastAPI é ilustrado na documentação oficial【43†L284-L286】【43†L294-L302】. Playwright facilita testes de apps em tempo real (captura SSE)【38†L208-L212】. LangAlpha exemplifica uma arquitetura multiagente com supervisor especializado【41†L335-L343】【41†L368-L376】. Daytona fornece sandboxes isolados para executar código gerado de forma segura【8†L110-L118】. Os desenvolvedores da OpenAI enfatizam a importância de limites de taxa e alertas de uso【17†L736-L744】. Diagrama abaixo ilustra a arquitetura recomendada do sistema:  

【41†embed_image】 *Figura: Arquitetura proposta (Next.js ↔ FastAPI ↔ LangGraph/Agentes ↔ PostgreSQL/Redis ↔ Sandbox)*  

【38†embed_image】 *Figura: Exemplo de teste e2e com Playwright interceptando SSE e renderizando resposta.*  

