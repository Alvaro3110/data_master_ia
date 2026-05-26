# Projeto agentic analytics para pricing, margem, safra, risco e ROAE

## Resumo executivo

A melhor leitura dos repositórios fornecidos é a seguinte: o **production-agentic-rag-course** entrega a espinha dorsal de um RAG de produção em quatro etapas bem claras — busca lexical com OpenSearch/BM25, busca híbrida com embeddings, resposta com LLM local e loop agentic com guardrails e reescrita de consulta; o **text2sql-framework** mostra um núcleo forte para dados estruturados, no qual o agente explora o schema diretamente com `execute_sql`, corrige a própria query e usa `scenarios.md` para regras de negócio; e o **LangAlpha** mostra como esse núcleo pode evoluir para um produto, com workspaces persistentes, execução programática de código em sandbox, skills, subagentes e frontend orientado a artefatos. Para um caso de uso de pricing/margem/safra/risco/ROAE, a arquitetura recomendada não é um “RAG puro de documentos”, mas um **produto híbrido**: RAG para glossário, políticas e regras; Text-to-SQL para dados estruturados; LangGraph para orquestração; e sandbox para análises e relatórios. citeturn1view0turn11view0turn11view4turn3view2turn5view0turn6view0turn6view2

Em termos de posicionamento para a banca, o projeto deve ser apresentado como **uma plataforma analítica conversacional governada**, desenhada para responder perguntas como “qual segmento teve pior margem na última safra?”, “quais clusters concentram pior ROAE ajustado a risco?” e “que regra de negócio explica determinada queda de margem?”. O valor de negócio está em reduzir tempo de análise, padronizar interpretação de métricas e dar rastreabilidade à resposta. O valor técnico está em combinar retrieval, execução segura de SQL, observabilidade, governança e camada agentic. citeturn5view0turn3view2turn6view0

A recomendação objetiva é construir o projeto em **duas trilhas simultâneas**. A primeira é o **MVP confiável**, com Next.js no frontend, FastAPI no backend, PostgreSQL como system of record, OpenSearch para catálogo/regras, DuckDB como opção local de desenvolvimento e testes, Ollama para inferência local, Jina para embeddings e LangGraph para orquestração. A segunda é a trilha de **hardening e produto**, inspirada no LangAlpha, com workspaces persistentes, sandbox de código, trilha de auditoria, skills, relatórios gerados e avaliação contínua por traces. Next.js oferece App Router com suporte às capacidades mais novas do React; FastAPI é um framework Python tipado e assíncrono para APIs; LangGraph é voltado a workflows stateful e de longa duração; OpenSearch suporta vetores e busca k-NN; DuckDB é um banco OLAP embutido; e Ollama expõe API local em `localhost:11434/api`, sem autenticação local por padrão. citeturn7search8turn7search1turn7search5turn7search2turn7search14turn7search11turn8search2turn8search5turn8search1turn8search7

O ponto crítico de governança é não seguir literalmente a tese “no RAG, no semantic layer, just execute_sql”, embora o **text2sql-framework** demonstre que esse loop autônomo pode funcionar muito bem em benchmarks e em schemas desconhecidos. Em ambiente corporativo sensível, especialmente com pricing e risco, o desenho robusto precisa de **whitelist de tabelas**, **masking**, **validação SQL**, **classificação de sensibilidade**, **limites de custo e cardinalidade**, **auditoria** e, em alguns casos, **aprovação humana**. O próprio framework mostra que `scenarios.md` é a peça correta para injetar semântica de negócio e que o loop melhora com análise de traces; a recomendação aqui é preservar essa força, mas sob uma camada explícita de controle. citeturn5view0

Os principais alvos de sucesso para a banca devem ser apresentados como metas de produto, e não como promessas absolutas, porque infraestrutura, volume de dados, modelo de LLM, throughput e cloud provider estão **não especificados**. Para um MVP crível, os alvos mais defensáveis são: **recall@5 ≥ 0,80** no RAG de regras, **taxa de execução SQL válida ≥ 85%** em suíte curada de perguntas, **P95 da resposta analítica ≤ 8s** em ambiente controlado local/cloud pequeno, **explicação com fontes/auditoria em 100% dos casos aprovados**, e **zero vazamento em testes de masking e controle de acesso**. Para a evolução a produto, esses alvos sobem em precisão, observabilidade e UX. Essa leitura é coerente com a ênfase do curso em métricas de relevância, otimização de latência, streaming e transparência do raciocínio, com a ênfase do text2sql em traces e cenários, e com a ênfase do LangAlpha em workspaces, governança e execução em sandbox. citeturn1view0turn2view6turn3view2turn5view0turn6view1turn6view2

## Contexto e síntese das referências

O **production-agentic-rag-course** ensina uma progressão que vale preservar. Na semana de OpenSearch, o curso assume que o caminho profissional começa por **keyword search first**: criar índice, mapear campos, transferir dados do PostgreSQL para o OpenSearch e testar BM25 com uma DAG de ingestão (`arxiv_paper_ingestion`) que busca na fonte, grava no PostgreSQL e indexa em OpenSearch. Na semana seguinte, a camada semântica entra por **chunking estruturado**, overlap e embeddings com Jina. Na semana seguinte, o pipeline vira RAG completo com **Ollama**, streaming e otimização de prompt. E, na etapa agentic, o fluxo deixa de ser linear e passa a ter **guardrail**, **grading de documentos**, **query rewriting** e **reasoning steps** expostos na resposta. citeturn1view0turn11view1turn11view2turn11view3turn11view4turn2view6turn3view2

Há quatro aprendizados especialmente valiosos do curso para o seu caso. O primeiro é a tese de que **retrieval lexical não deve ser pulado**, o que faz sentido inclusive para tabelas e documentação corporativa: nomes de métricas, códigos de produto e rótulos de safra costumam responder bem a busca lexical. O segundo é que chunking bom exige estrutura; no notebook de hybrid search, a função `section_based_chunking` opera com **600 palavras por chunk e 100 palavras de overlap**, com recomendação explícita de 100 palavras como melhor equilíbrio. O terceiro é que a fusão híbrida do exemplo usa **60% BM25 + 40% vetor**. O quarto é que a semana agentic define um **threshold de guardrail 60/100** e **no máximo duas tentativas de retrieval**, expondo `reasoning_steps`, `retrieval_attempts` e `rewritten_query`. citeturn1view0turn11view1turn11view3turn3view2

O **text2sql-framework** traz a peça central para o mundo estruturado: ele argumenta que, com modelos recentes capazes de longos loops de ferramentas, a geração de SQL pode ocorrer no **mesmo loop** em que o agente descobre schema, testa queries, lê erros e corrige o plano. O README oficial é explícito: a proposta é dar ao agente um `execute_sql`, sem RAG ou semantic layer obrigatórios, e deixar o agente explorar o banco. O framework também acrescenta um elemento decisivo para ambiente corporativo: o arquivo **`scenarios.md`**, consultado via `lookup_example`, para transmitir semântica que schema nenhum revela sozinho, como regra de “receita líquida”, caminho correto de join ou tradução entre jargão de negócio e coluna física. Além disso, o projeto registra **traces** e oferece um loop de melhoria via MCP para analisar erros recorrentes e produzir novos cenários. citeturn5view0

O **LangAlpha** é a principal referência de “MVP para produto”. Ele parte de um problema diferente — pesquisa financeira — mas introduz padrões que são diretamente transferíveis para pricing e risco: **workspaces persistentes**, `agent.md` como memória operacional do projeto, **Programmatic Tool Calling** para processar dados em Python dentro de um sandbox, **skills**, **subagentes paralelos**, **SSE/WebSocket**, filas em Redis e estado persistido em PostgreSQL. Sua arquitetura usa frontend React 19/Vite/Tailwind e backend FastAPI, com sandboxes Daytona, Redis e Postgres; para o seu projeto, isso não precisa ser copiado literalmente, mas deve inspirar o design do produto final. citeturn6view0turn6view1turn6view2turn6view3

A síntese mais robusta para o seu projeto é esta: **curso = retrieval e serving**, **text2sql = núcleo analítico estruturado**, **LangAlpha = plataforma e UX de produto**. Essa combinação é superior a qualquer uma das peças isoladamente para o caso de pricing, porque pricing exige tanto **explicar regras** quanto **consultar fatos**, e ainda precisa transformar o resultado em **artefato executivo**. citeturn11view4turn5view0turn6view0

A tabela abaixo resume os trade-offs centrais entre as abordagens, já traduzidos para o caso de uso de pricing e risco.

| Abordagem | Melhor uso | Vantagem principal | Risco principal | Papel no projeto recomendado |
|---|---|---|---|---|
| RAG documental | Glossário, política, normas de pricing, definição de ROAE e regras de safra | Explica semântica e traz evidência textual | Não responde bem a fatos tabulares e agregações | Camada de contexto e justificativa |
| Text-to-SQL agent | Métricas, cortes, agregações, comparativos por safra/segmento/produto | Recupera fatos diretamente da base | Sem guardrails pode errar schema, custo ou confidencialidade | Camada factual principal |
| Padrão LangAlpha | Produto final com memória, artefatos, análises e relatórios | Dá continuidade, sandbox, skills e UX de produto | Maior escopo, maior esforço e mais superfície operacional | Norte de evolução para produto |
| Course-style Agentic RAG | Orquestração, guardrails, reescrita e retries | Mais confiabilidade operacional | Pode degradar se o estado do agente for mal definido | Camada de decisão e controle |

Essa matriz é uma síntese analítica dos repositórios oficiais: o curso enfatiza retrieval híbrido, otimização e guardrails; o text2sql enfatiza o loop de exploração do banco com `execute_sql` e cenários; e o LangAlpha enfatiza workspaces, PTC, subagentes e infraestrutura de produto. citeturn11view0turn11view4turn3view2turn5view0turn6view0turn6view2

## Escopo do produto e requisitos

### Objetivos, público e premissas

O objetivo do produto é oferecer um **copilot analítico governado** para pricing, margem, safra, risco e ROAE. Em termos de usuário, ele deve responder três grandes classes de perguntas. A primeira é **conceitual**: “o que é margem líquida ajustada ao risco?”; “qual regra define alto risco?”; “o que significa safra nesta base?”. A segunda é **analítica**: “qual segmento teve pior margem na última safra?”; “compare ROAE e inadimplência por safra”; “mostre clusters de baixa margem e alto risco”. A terceira é **executiva**: “gere um relatório com diagnóstico e recomendações”, “crie uma visão resumida para comitê”. O produto recomendado nasce da fusão entre o padrão de retrieval e geração do curso, o motor exploratório do text2sql e a noção de workbench orientado a artefatos do LangAlpha. citeturn11view4turn3view2turn5view0turn6view0

O público da banca é misto. Para avaliadores técnicos, o valor estará em arquitetura, segurança, observabilidade, testes, clareza do agente e escalabilidade da stack. Para avaliadores de negócio, o foco precisa estar em tempo de resposta, rastreabilidade, qualidade do insight e redução de trabalho manual. Por isso, o storytelling da banca deve sempre mostrar a cadeia “**pergunta → regra recuperada → SQL seguro → evidência → insight → relatório**”. Essa cadeia conecta claramente a semântica do negócio à execução de dados, o que é exatamente a lacuna entre RAG puro e analytics tradicional. citeturn5view0turn6view0

Alguns itens permanecem **não especificados** e devem ser assumidos como parâmetros do projeto, não como premissas fixas: cloud provider, provedor de autenticação, volumes reais de dados, requisitos formais de LGPD setorial, SLA final, volume de usuários concorrentes, hardware do ambiente local, política de segregação de ambientes e catálogo corporativo existente. Esses pontos devem aparecer explicitamente no material da banca como “decisões de implantação pendentes”. 

### Requisitos funcionais

Os requisitos funcionais recomendados para o MVP e para o caminho a produto podem ser organizados da seguinte forma:

| Domínio | Requisito |
|---|---|
| Perguntas conceituais | Buscar definições, regras e exceções em glossário, documentação e políticas |
| Perguntas analíticas | Gerar SQL apenas de leitura, executar com limites e devolver tabela, resumo e fonte |
| Governança | Classificar pergunta, validar escopo, aplicar perfil de acesso e mascarar dados sensíveis |
| Agente | Reescrever pergunta vaga, decidir entre RAG, Text-to-SQL ou ambos, e registrar reasoning steps |
| Relatórios | Gerar resumo executivo, tabela, gráfico simples e artefato exportável |
| Auditoria | Registrar pergunta, plano, SQL final, tempo, custo estimado, fontes consultadas, usuário e resultado |
| Observabilidade | Exibir trace id e status por etapa |
| UX | Permitir chat, histórico, visualização de SQL, fontes, filtros e download de relatório |

Esses requisitos são aderentes ao que o curso já demonstra em retrieval, streaming e agentic loop, ao que o text2sql já demonstra em exploração e correção automática e ao que o LangAlpha mostra em workspaces, artefatos e execução assíncrona. citeturn11view4turn3view2turn5view0turn6view1turn6view3

### Requisitos não funcionais

Os requisitos não funcionais devem ser apresentados como metas de engenharia. Recomenda-se adotar, no mínimo, os seguintes critérios:

| Categoria | Meta inicial recomendada |
|---|---|
| Disponibilidade | Não especificado para MVP; meta alvo de produto: 99,5% em horário comercial |
| Latência | P95 de `/search-rules` ≤ 1,5s; P95 de `/ask-analytics` ≤ 8s em ambiente de referência |
| Segurança | Zero exposição de colunas mascaradas na suíte de segurança |
| Auditabilidade | 100% das respostas com `trace_id`; 100% das queries executadas com log |
| Reprodutibilidade | Toda resposta analítica deve carregar SQL executado ou justificativa de não execução |
| Testabilidade | Cobertura de fluxos críticos ≥ 85% e suíte E2E validando caminhos principais |
| Custos | Orçamento por consulta monitorado; bloqueio de planos acima do limite definido |
| Escalabilidade | Horizontal no backend; desacoplamento entre UI, API e executor |

A justificativa técnica para Next.js, FastAPI, LangGraph, OpenSearch, DuckDB e Ollama é coerente com as capacidades oficiais desses projetos: Next.js organiza aplicações modernas com App Router; FastAPI é tipado e assíncrono; LangGraph foi desenhado para workflows stateful; OpenSearch combina texto e vetores; DuckDB é OLAP embutido; e Ollama expõe API local simples para modelos locais. citeturn7search8turn7search1turn7search5turn7search2turn7search14turn8search2turn8search5turn8search1

## Arquitetura recomendada

### Visão arquitetural

A arquitetura recomendada separa claramente **semântica**, **fatos** e **orquestração**. Semântica fica no RAG de regras; fatos vêm do banco estruturado; e a decisão de qual caminho usar é do grafo agentic. O frontend deve ser em **Next.js** — mesmo que o LangAlpha use React/Vite — porque o App Router e o modelo híbrido de Server/Client Components ajudam a manter UX, autenticação e rotas organizadas em uma solução mais “produto”. O backend deve ser em **FastAPI** por aderência ao ecossistema Python do curso, do text2sql e do LangGraph. A orquestração deve ser em **LangGraph**, porque a natureza stateful e ciclíca do fluxo agentic não é bem representada por um pipeline linear simples. O armazenamento factual deve ser **PostgreSQL** em produção e **DuckDB** como opção local ou analítica controlada. O catálogo e a camada de regras podem usar **OpenSearch** para busca lexical e vetorial. Para embeddings, faz sentido manter **Jina Embeddings v3**, já usada no curso, com 1024 dimensões como baseline. Para inferência, o desenho deve ser provider-agnostic: **Ollama** local por privacidade e custo controlado; **OpenAI** ou outro provedor de fronteira como opção para ambientes que precisem de mais qualidade. citeturn7search8turn7search1turn7search2turn1view0turn11view1turn11view2turn7search14turn8search0turn8search1turn8search7

```mermaid
flowchart LR
    U[Usuário] --> FE[Next.js Frontend]
    FE --> API[FastAPI Backend]
    API --> AUTH[AuthN/AuthZ]
    API --> ORCH[LangGraph Orchestrator]

    ORCH --> G1[Guardrail & Intent Router]
    ORCH --> RAG[RAG de Regras]
    ORCH --> TSQL[Text2SQL Agent]
    ORCH --> REPO[Report Generator]

    RAG --> OS[OpenSearch]
    RAG --> EMB[Embeddings Jina]
    TSQL --> VAL[SQL Validator & Query Planner]
    VAL --> EXEC[Secure SQL Executor]
    EXEC --> PG[(PostgreSQL)]
    EXEC --> DD[(DuckDB opcional)]

    ORCH --> SBX[Sandbox de Código]
    SBX --> FS[Artefatos / Relatórios]
    API --> AUD[Audit & Tracing]
    AUD --> PG
    FE --> FS

    classDef core fill:#eef,stroke:#446;
    classDef data fill:#efe,stroke:#484;
    class API,ORCH,G1,RAG,TSQL,VAL,EXEC,REPO core;
    class OS,EMB,PG,DD,SBX,FS,AUD data;
```

Essa proposta herda do curso a separação entre ingestão, indexação, busca e geração; do text2sql, o loop de descoberta/correção; e do LangAlpha, o uso de sandbox, artefatos, workspaces e orquestração assíncrona. O LangAlpha, especificamente, descreve uma arquitetura com frontend web, FastAPI, PostgreSQL, Redis, sandboxes Daytona e workflow agentic; o desenho acima é uma adaptação dessa lógica para um produto de analytics governado. citeturn1view0turn11view4turn3view2turn6view1turn6view2

### Fluxo agentic

O coração do sistema deve ser um fluxo orientado por decisão, e não por chamada única ao LLM. A ideia central é aproveitar a lógica do Week 7 — guardrail, grading, rewrite e retry — e estendê-la para structured analytics. O guardrail avalia escopo, sensibilidade e intenção; o router decide se o caso é conceitual, analítico ou híbrido; o RAG recupera regras se a pergunta exige contexto; o Text-to-SQL monta o plano factual; o executor seguro roda apenas aquilo que passou nos validadores; e o gerador de relatório monta a resposta em linguagem de negócio. citeturn3view2turn5view0turn6view0

```mermaid
flowchart TB
    A[Pergunta] --> B[Guardrail]
    B -->|fora de escopo| X[Resposta orientativa]
    B -->|escopo válido| C[Classificar intenção]

    C -->|conceitual| D[RAG de regras]
    C -->|analítica| E[Gerar SQL]
    C -->|híbrida| D

    D --> F[Contexto semântico]
    F --> E

    E --> G[Validação SQL]
    G -->|bloqueado| H[Reescrever pergunta ou pedir refinamento]
    H --> C

    G -->|válido| I[Executar com limites]
    I -->|sem dados ou erro| J[Query rewriting / retry]
    J --> E

    I -->|ok| K[Explicar resultado]
    K --> L[Gerar tabela, resumo e relatório]
    L --> M[Auditar, traçar e responder]
```

O paralelo com o Week 7 é direto: lá o guardrail usa score 0–100 e corta abaixo de 60, os documentos são avaliados, e a consulta pode ser reescrita em até duas tentativas; aqui a mesma disciplina é aplicada ao mundo estruturado, trocando “document relevance” por “plano SQL válido e resultado útil”. citeturn3view2

### Componentes e responsabilidades

| Componente | Responsabilidade principal | Inspiração dominante |
|---|---|---|
| Next.js frontend | Chat, filtros, histórico, SQL viewer, fontes, relatórios e downloads | recomendação arquitetural sobre stack web |
| FastAPI backend | APIs, autenticação, rate limiting, tracing, composição de respostas | course + LangAlpha |
| LangGraph agent | Guardrails, roteamento, retries, reasoning steps e coordenação | Week 7 + LangAlpha |
| Text2SQL agent | Explorar schema, planejar SQL, autocorrigir e usar cenários | text2sql-framework |
| OpenSearch | Buscar glossário, regras, políticas e documentação com lexical + vector | Weeks 3–4 |
| PostgreSQL | System of record, auditoria, perfis, histórico e dados operacionais | Weeks 3–4 + LangAlpha |
| DuckDB | Ambiente local, snapshot analítico, testes e datasets de demonstração | nossa recomendação |
| Ollama / OpenAI | Geração, reformulação e explicação; local ou cloud | Week 5 + opção de provider |
| Jina | Embeddings para RAG de regras e catálogo | Week 4 |
| Sandbox | Python/SQL/artefatos, gráficos e relatórios | LangAlpha |

### Modelo de dados proposto

O modelo de dados deve ser simples o suficiente para o MVP e extensível o suficiente para o produto. O ponto central é separar **camada factual**, **camada semântica**, **camada operacional** e **camada de auditoria**.

| Tabela / índice | Papel | Campos recomendados |
|---|---|---|
| `fact_pricing_snapshot` | fatos de pricing por safra/cliente/produto | `snapshot_id`, `safra`, `cliente_id`, `segmento`, `produto`, `receita`, `custo`, `margem_liquida`, `roae`, `score_risco`, `inadimplente`, `status_cliente` |
| `dim_cliente` | atributos do cliente | `cliente_id`, `porte`, `segmento`, `uf`, `rating`, `faixa_risco`, `is_pii_masked` |
| `dim_produto` | atributos de produto | `produto_id`, `produto`, `familia`, `garantia`, `prazo` |
| `metric_catalog` | catálogo de métricas | `metric_id`, `nome_logico`, `descricao`, `formula`, `owner`, `sensibilidade` |
| `semantic_rule_docs` | fonte primária do RAG | `doc_id`, `titulo`, `tipo`, `texto`, `tags`, `versionamento`, `vigencia_inicio`, `vigencia_fim` |
| `semantic_rule_chunks` | índice de chunks | `chunk_id`, `doc_id`, `texto`, `embedding`, `tags`, `source_url`, `version` |
| `schema_catalog` | catálogo de schema para agentes | `table_name`, `column_name`, `data_type`, `business_name`, `sensitivity`, `allowed_roles` |
| `agent_sessions` | contexto operacional | `session_id`, `user_id`, `workspace_id`, `status`, `model`, `created_at` |
| `query_audit_log` | trilha de auditoria | `audit_id`, `trace_id`, `session_id`, `question`, `routed_path`, `sql_final`, `status`, `latency_ms`, `estimated_cost`, `masked_fields`, `created_at` |
| `report_artifacts` | resultados salvos | `artifact_id`, `trace_id`, `type`, `path`, `summary`, `created_at` |

A recomendação de manter um catálogo semântico separado é coerente com o curso, que separa PostgreSQL de OpenSearch, e com o text2sql, que separa schema físico de semântica em `scenarios.md`. Já a ideia de workspaces, artefatos e notas persistentes vem do LangAlpha. citeturn1view0turn5view0turn6view0

### Fluxos operacionais

O fluxo completo do produto deve seguir a cadeia abaixo:

| Etapa | Descrição |
|---|---|
| Ingestão | Carregar fatos de pricing/risco/ROAE no PostgreSQL ou snapshot local em DuckDB |
| Catalogação | Atualizar `schema_catalog`, `metric_catalog` e governança de acesso |
| RAG de regras | Indexar glossário, políticas, fórmulas e exceções em OpenSearch |
| Text-to-SQL | Gerar e corrigir SQL com base em intenção, schema e cenários |
| Executor seguro | Validar, limitar e executar apenas leitura |
| Agentic loop | Reescrever consulta, trocar estratégia e repetir se necessário |
| Geração de relatório | Produzir explicação, tabela, gráfico e artefato exportável |
| Auditoria | Persistir `trace_id`, fontes, SQL, mascaramentos e tempos |

## Segurança, governança, métricas e TDD

### Segurança e governança

A pior decisão possível neste projeto seria tratar o LLM como um “superusuário amigável”. O desenho seguro precisa impor o contrário: **o agente deve operar sob um perfil de menor privilégio e com alto nível de explicitude**. Recomenda-se uma arquitetura de governança em cinco camadas. A primeira é **controle de escopo**, derivado do Week 7: perguntas fora do domínio ou proibidas devem ser rejeitadas antes de retrieval ou SQL. A segunda é **classificação de sensibilidade** por tabela e coluna, ligada ao `schema_catalog`. A terceira é **validação SQL semântica e sintática**, impondo apenas `SELECT`, bloqueando `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `DROP`, `COPY`, `UNLOAD`, CTEs perigosas e consultas sem `LIMIT` ou sem partição temporal quando exigido. A quarta é **masking e agregação seguros**, com proibição de granularidade cliente quando a política exigir apenas nível agregado. A quinta é **auditoria e tracing**, com gravação do plano, SQL final, colunas tocadas, decisão de masking, custo e resultado. O curso já mostra a importância de tracing e reasoning steps; o LangAlpha reforça sandbox, redaction e armazenamento seguro; e o text2sql destaca traces como insumo para melhoria. citeturn3view2turn6view1turn5view0

A política mínima de segurança recomendada para banca é a seguinte:

| Controle | Recomendação objetiva |
|---|---|
| Tabelas permitidas | whitelist por role e por ambiente |
| Colunas sensíveis | classificação `PUBLICA`, `INTERNA`, `SENSIVEL`, `RESTRITA` |
| SQL permitido | somente leitura; sem múltiplas statements |
| Limites | `LIMIT` obrigatório, timeout, orçamento estimado de linhas e bytes |
| Masking | hash, truncamento, bucketização ou supressão de identificadores |
| Aprovação humana | opcional para consultas caras ou sensíveis |
| Logs | persistir pergunta, rota, SQL, plano, trace id e artefato |
| Segredos | fora do prompt; em secret manager ou vault |
| Sandbox | execução isolada, sem acesso irrestrito à rede |
| Versionamento | versionar regras, prompts e cenários |

No caso do RAG de regras, a governança também exige versionamento documental. “O que é safra?” ou “qual fórmula de ROAE vale?” pode mudar com política interna; logo, a indexação precisa guardar vigência e versão. No caso do Text-to-SQL, `scenarios.md` não deve ser um arquivo solto: deve ser tratado como **repositório semântico governado**, talvez desmembrado em várias regras versionadas no banco e exportado para contexto do agente no build. Isso preserva a vantagem do framework sem abrir mão de trilha de mudança. citeturn5view0

### Métricas de sucesso

As métricas precisam ser apresentadas em quatro frentes: **qualidade de retrieval**, **qualidade analítica**, **eficiência operacional** e **segurança**. O curso já trabalha com relevância, latência e otimização; o text2sql trabalha com sucesso do loop e traces; e o LangAlpha trabalha com produção, workspaces e automações. A recomendação é transformar isso em um scorecard de produto. citeturn1view0turn2view6turn5view0turn6view1

| Categoria | Métrica | MVP | Produto |
|---|---|---:|---:|
| RAG de regras | Recall@5 | ≥ 0,80 | ≥ 0,90 |
| RAG de regras | Precision@5 | ≥ 0,70 | ≥ 0,85 |
| Text-to-SQL | SQL válido sintaticamente | ≥ 90% | ≥ 97% |
| Text-to-SQL | Execução correta em benchmark interno | ≥ 85% | ≥ 92% |
| End-to-end | Resposta útil aprovada por avaliador | ≥ 80% | ≥ 90% |
| Operação | P95 latência `/ask-analytics` | ≤ 8s | ≤ 5s |
| Operação | Custo médio por pergunta | medido e controlado | otimizado por tier |
| Segurança | Vazamentos nos testes | 0 | 0 |
| Auditoria | Respostas com `trace_id` | 100% | 100% |
| Relatórios | Geração de artefato executivo | ≥ 70% | ≥ 90% |

Como os notebooks do curso foram desenvolvidos em ambiente local e com dados acadêmicos, e o text2sql reporta benchmark próprio sobre Spider em uma configuração específica, esses números devem ser apresentados como **metas internas do projeto**, e não como resultados automaticamente herdados dos repositórios. citeturn2view6turn5view0

### Estratégia TDD

A suíte TDD precisa ser pensada por camadas. O componente mais crítico não é a tela, mas o **caminho de decisão**. Por isso, a recomendação é que a base do TDD cubra: guardrails, roteamento de intenção, validação SQL, masking, limitação de custo, execução segura, auditoria e geração da resposta final. O uso de **pytest** é consistente para unidade e integração em Python, e o uso de **Playwright com plugin oficial para pytest** é consistente para E2E em frontend. Para testes de integração HTTP, `requests` continua sendo suficiente e simples. citeturn10search4turn10search3turn10search2

| Camada | Foco | Ferramenta |
|---|---|---|
| Unitária | parser, guardrail, validator, masker, planner | pytest |
| Integração | API + OpenSearch + executor + DB | pytest + requests + docker compose |
| Contrato | schemas de request/response | pytest + pydantic |
| E2E | jornada do usuário no frontend | Playwright |
| Segurança | SQL injection, bypass, vazamento, custo | pytest |
| Observabilidade | geração de `trace_id`, auditoria e logs | pytest |

### Casos de teste automatizados

A tabela abaixo distribui o TDD por componente e fluxo crítico.

| Componente / fluxo | Casos unitários | Casos de integração | E2E / segurança | Critério automatizado |
|---|---|---|---|---|
| Guardrail | fora de escopo, escopo válido, sensibilidade alta | endpoint rejeita pergunta proibida | UI mostra recusa explicável | status 200/4xx e `reasoning_steps` coerente |
| Intent router | conceitual vs analítico vs híbrido | rota correta chama RAG/SQL | UX mostra fontes ou SQL conforme rota | `routed_path` esperado |
| RAG de regras | chunks corretos, ranking, deduplicação | OpenSearch retorna docs válidos | pergunta conceitual mostra fontes | recall@k mínimo |
| SQL generator | mapeia métricas, joins, filtros temporais | query executa em DB seed | UI exibe SQL final | SQL válido e resultado esperado |
| SQL validator | bloqueia DDL/DML, multi-statement, full scan | API rejeita query perigosa | exploração maliciosa falha | `allowed=False` |
| Masking | PII vira hash/bucket | resultado sensível nunca volta sem máscara | UI nunca renderiza identificador puro | `masked_fields` preenchido |
| Cost limiter | estima custo, aplica timeout/limit | query cara é abortada | UX recebe explicação amigável | erro controlado |
| Auditoria/tracing | gera `trace_id`, persiste log | log gravado após cada execução | trace visível/consultável | linha inserida no audit log |
| Report generator | resumo executivo, tabela e gráfico | artefato salvo | download no frontend | arquivo existe e metadata ok |

### Exemplos de testes

#### Testes unitários com pytest

```python
# tests/unit/test_sql_validator.py
import pytest
from app.security.sql_validator import validate_sql

def test_bloqueia_ddl():
    verdict = validate_sql("DROP TABLE fact_pricing_snapshot;")
    assert verdict.allowed is False
    assert "DROP" in verdict.reasons[0]

def test_bloqueia_multistatement():
    verdict = validate_sql("SELECT * FROM fact_pricing_snapshot; DELETE FROM users;")
    assert verdict.allowed is False
    assert "multiple statements" in " ".join(verdict.reasons).lower()

def test_exige_limit_para_tabela_grande():
    verdict = validate_sql("SELECT * FROM fact_pricing_snapshot")
    assert verdict.allowed is False
    assert verdict.rewrite_hint is not None

def test_permite_select_agregado():
    verdict = validate_sql("""
        SELECT safra, AVG(margem_liquida) AS margem_media
        FROM fact_pricing_snapshot
        WHERE safra = '2026-03'
        GROUP BY safra
        LIMIT 100
    """)
    assert verdict.allowed is True
```

```python
# tests/unit/test_masking.py
from app.security.masking import apply_masking

def test_mascaramento_cliente():
    rows = [{"cliente_id": "12345678900", "margem_liquida": 10.5}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert masked[0]["cliente_id"] != "12345678900"
    assert masked[0]["margem_liquida"] == 10.5
```

```python
# tests/unit/test_guardrail.py
from app.agent.guardrail import classify_question

def test_guardrail_rejeita_fora_de_escopo():
    res = classify_question("Qual é a capital da França?")
    assert res.allowed is False
    assert res.score < 60

def test_guardrail_aceita_pergunta_de_pricing():
    res = classify_question("Qual segmento teve pior margem na última safra?")
    assert res.allowed is True
    assert res.intent in {"analytics", "hybrid"}
```

#### Testes de integração com pytest e requests

```python
# tests/integration/test_ask_analytics.py
import requests

BASE_URL = "http://localhost:8000"

def test_fluxo_hibrido_com_regras_e_sql():
    payload = {
        "question": "Explique a regra de alto risco e compare ROAE por safra nos clientes de alto risco",
        "workspace_id": "demo",
        "mode": "auto"
    }
    resp = requests.post(f"{BASE_URL}/api/v1/ask-analytics", json=payload, timeout=30)
    assert resp.status_code == 200

    data = resp.json()
    assert data["trace_id"]
    assert data["routed_path"] in {"hybrid", "analytics"}
    assert "reasoning_steps" in data
    assert "answer" in data
    assert "sources" in data
    assert "sql" in data or data["routed_path"] == "rules_only"
```

```python
# tests/integration/test_cost_limit.py
import requests

BASE_URL = "http://localhost:8000"

def test_query_cara_e_abortada():
    payload = {
        "question": "Liste cada cliente com todos os campos históricos desde o início da base",
        "workspace_id": "demo",
        "mode": "auto"
    }
    resp = requests.post(f"{BASE_URL}/api/v1/ask-analytics", json=payload, timeout=30)
    assert resp.status_code in {200, 422}
    data = resp.json()
    assert data["status"] in {"blocked", "refined", "rejected"}
    assert "cost" in data["reasoning_steps"][-1].lower() or data.get("estimated_cost") is not None
```

```python
# tests/integration/test_audit.py
import requests
import psycopg

BASE_URL = "http://localhost:8000"
DSN = "postgresql://app:app@localhost:5432/app"

def test_auditoria_persistida():
    payload = {"question": "Qual produto teve pior margem na safra 2026-03?", "workspace_id": "demo"}
    resp = requests.post(f"{BASE_URL}/api/v1/ask-analytics", json=payload, timeout=30)
    assert resp.status_code == 200
    trace_id = resp.json()["trace_id"]

    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status, question FROM query_audit_log WHERE trace_id = %s", (trace_id,))
            row = cur.fetchone()

    assert row is not None
    assert row[0] in ("success", "blocked", "partial_success")
```

#### Testes E2E com Playwright

```python
# tests/e2e/test_frontend_chat.py
from playwright.sync_api import Page, expect

def test_usuario_gera_relatorio_de_margem(page: Page):
    page.goto("http://localhost:3000")
    page.get_by_placeholder("Pergunte sobre margem, safra, risco ou ROAE").fill(
        "Gere um diagnóstico executivo da margem por safra para clientes de alto risco"
    )
    page.get_by_role("button", name="Analisar").click()

    expect(page.get_by_text("Trace ID")).to_be_visible(timeout=20000)
    expect(page.get_by_text("SQL executado")).to_be_visible(timeout=20000)
    expect(page.get_by_text("Resumo executivo")).to_be_visible(timeout=20000)
    expect(page.get_by_role("button", name="Baixar relatório")).to_be_visible(timeout=20000)
```

```python
# tests/e2e/test_security_masking.py
from playwright.sync_api import Page, expect

def test_ui_nao_vaza_identificador_sensivel(page: Page):
    page.goto("http://localhost:3000")
    page.get_by_placeholder("Pergunte sobre margem, safra, risco ou ROAE").fill(
        "Liste os clientes com pior margem na última safra"
    )
    page.get_by_role("button", name="Analisar").click()

    expect(page.get_by_text("cliente_id")).not_to_be_visible(timeout=20000)
    expect(page.get_by_text("CPF")).not_to_be_visible(timeout=20000)
    expect(page.get_by_text("Dados mascarados")).to_be_visible(timeout=20000)
```

### Critérios de aceitação automatizados

| Fluxo | Critério de aceite |
|---|---|
| Pergunta fora de escopo | resposta sem SQL, com rejeição clara e `retrieval_attempts=0` |
| Pergunta conceitual | resposta com fontes de regras e sem execução SQL desnecessária |
| Pergunta analítica | resposta com SQL final, tabela e explicação |
| Pergunta híbrida | resposta com fontes + SQL + explicação |
| Query maliciosa | bloqueio antes da execução |
| Dado sensível | retorno sempre mascarado ou agregado |
| Custo excessivo | bloqueio ou refinamento automático |
| Auditoria | `trace_id` + registro persistido |
| Relatório | artefato salvo e acessível |

## Plano de implementação e evolução

### Milestones

A recomendação é dividir a construção em milestones que possam ser executados por agentes de coding com baixo acoplamento. O pacote de handoff para implementação deve conter `AGENTS.md`, `TASKS.md`, `ARCHITECTURE.md`, `PROMPTS.md`, `EVALS.md`, `SECURITY.md` e seeds de dados. Essa forma de decomposição conversa bem com uma implementação assistida por Antigravity/Codex, mas também é saudável para qualquer time humano. 

| Milestone | Escopo | Saída principal | Esforço estimado |
|---|---|---|---:|
| Fundação | monorepo, FastAPI, Next.js, docker, auth placeholder, tracing base | app sobe local e healthchecks | 40–60h |
| Dados e catálogo | PostgreSQL/DuckDB, seeds, schema catalog, metric catalog, OpenSearch para regras | bases carregadas e indexadas | 50–80h |
| Núcleo agentic | guardrail, router, RAG rules, Text2SQL loop, SQL validator | endpoint `/ask-analytics` funcional | 90–140h |
| UX e relatórios | chat UI, viewer de SQL/fontes, export de relatório | demo end-to-end | 60–100h |
| Hardening | masking, custo, auditoria, testes E2E, benchmark | versão de banca estável | 70–110h |
| Produto | workspace persistente, sandbox, skills, async jobs, agenda | plataforma evoluída | 180–320h |

### Estimativa de esforço

Como o ambiente de implantação é **não especificado**, a melhor forma de estimar é por capacidade de entrega. Abaixo, uma estimativa realista para três configurações de equipe.

| Perfil de equipe | Composição | MVP | Produto |
|---|---|---:|---:|
| Enxuta | 1 full-stack sênior + 1 analista/QA parcial | 260–360h | 560–760h |
| Balanceada | 1 backend/agent + 1 frontend + 1 data/QA parcial | 300–420h | 650–900h |
| Forte | 1 tech lead + 1 backend + 1 frontend + 1 data/QA | 280–380h | 620–850h |

Para banca, a estimativa mais defensável costuma ser a **equipe balanceada**, com MVP em 6 a 8 semanas corridas e evolução para produto em 12 a 16 semanas, dependendo da disponibilidade. 

### Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| SQL incorreto em perguntas ambíguas | média | alto | gold set interno, cenários versionados, validação por execução |
| Vazamento de dado sensível | baixa/média | crítico | masking obrigatório, roles, testes de segurança, logs |
| Latência alta com LLM local | média | médio/alto | cache, prompts enxutos, modelos distintos por tarefa |
| OpenSearch desnecessário ou subutilizado | média | médio | usar apenas para regras/glossário e não para fatos tabulares |
| Escopo inflado pelo modelo LangAlpha | alta | alto | separar MVP de produto, backlog por fases |
| Dependência excessiva do prompt | média | alto | TDD, traces, cenários e critérios automatizados |
| Custos imprevisíveis em cloud LLM | média | médio | provider-agnostic, budget guardrails, fallback local |
| Drift de regra de negócio | alta | alto | versionamento de regra, vigência e owner por documento |

### Fases de evolução inspiradas no LangAlpha

A evolução recomendada em cinco fases, inspirada no LangAlpha, deve ser explícita na banca para mostrar maturidade de roadmap.

| Fase | Objetivo | Capacidade-chave |
|---|---|---|
| Fundamentos governados | construir o núcleo seguro | RAG de regras + Text-to-SQL + validação + auditoria |
| Copilot analítico | melhorar UX e explainability | chat, SQL viewer, fontes, relatórios simples |
| Workspace persistente | dar continuidade ao trabalho | histórico, `agent.md`, artefatos por workspace |
| PTC e sandbox | análises ricas | Python em sandbox, gráficos, decomposição de drivers |
| Skills e automações | virar produto | playbooks de pricing, agenda, notificações e subagentes |

Essa trilha reproduz o salto que o LangAlpha faz de “agente que responde” para “plataforma que trabalha”. No seu caso, as skills mais naturais seriam coisas como **/comparar_safras**, **/auditar_margem**, **/analisar_risco**, **/gerar_book_precificacao** e **/resumir_comite**. A referência conceitual é o modelo de skills, workspaces e swarm do LangAlpha. citeturn6view0turn6view3

## Material pronto para banca

### Prompts prontos

Os prompts abaixo já estão adaptados para o caso de pricing. Todos devem retornar JSON estrito sempre que possível.

#### Prompt de guardrail

```text
Você é o guardrail de um sistema analítico governado para pricing, margem, safra, risco e ROAE.

Sua tarefa é classificar a pergunta do usuário e devolver JSON válido.

Regras:
- O domínio permitido inclui: pricing, margem, spread, safra, risco, ROAE, rentabilidade, produto, segmento, cluster, carteira, inadimplência, garantia, política comercial, regras de negócio, documentação técnica e métricas relacionadas.
- Se a pergunta estiver fora do domínio, marque allowed=false.
- Se a pergunta pedir ação destrutiva, extração massiva de dados sensíveis, ou instruções que violem política de acesso, marque allowed=false.
- Se a pergunta estiver no domínio, defina intent como:
  - "conceptual" para definição/regra/política
  - "analytics" para consulta quantitativa/tabular
  - "hybrid" quando exigir regra + dado
- Dê um score de 0 a 100.
- Sugira rewrite apenas se a pergunta estiver vaga, mas ainda válida.
- Nunca gere SQL.
- Nunca invente tabela ou coluna.

Saída JSON:
{
  "allowed": true,
  "score": 0,
  "intent": "conceptual|analytics|hybrid|out_of_scope",
  "rewrite_suggestion": null,
  "sensitivity_flag": "low|medium|high",
  "reason": "..."
}

Pergunta:
{{question}}
```

#### Prompt de query rewriting

```text
Você reescreve perguntas para maximizar a precisão de um sistema agentic analytics.

Objetivo:
- Tornar a pergunta mais específica, sem mudar a intenção do usuário.
- Preservar dimensões de negócio, filtros temporais e métricas implícitas.
- Se houver ambiguidade em "última safra", "alto risco", "margem", "ROAE", explicite o conceito usando termos corporativos neutros.
- Não invente colunas físicas.
- Não gere SQL.
- A saída deve ser curta e operacional.

Retorne JSON:
{
  "rewritten_question": "...",
  "why": "...",
  "assumptions": ["..."]
}

Pergunta original:
{{question}}

Contexto opcional:
{{retrieval_feedback}}
{{guardrail_result}}
```

#### Prompt de geração de SQL

```text
Você é um agente Text-to-SQL corporativo para analytics de pricing.

Objetivo:
- Gerar uma consulta SQL somente leitura, segura e auditável.
- Use apenas tabelas e colunas autorizadas pelo schema_catalog.
- Respeite as regras de negócio presentes em scenarios e docs.
- Prefira resultados agregados.
- Inclua LIMIT quando aplicável.
- Se a pergunta exigir detalhe sensível no nível cliente e a política impedir, devolva bloqueio em vez de SQL.
- Não use DDL, DML, stored procedures, COPY, UNLOAD, CALL, GRANT, REVOKE, CREATE TEMP, multiple statements.
- Quando a pergunta mencionar período e houver coluna safra, filtre por safra.
- Quando a pergunta mencionar “alto risco”, consulte primeiro a regra do cenário/semântica; não assuma faixa arbitrariamente.
- Responda em JSON estrito.

Saída:
{
  "decision": "sql|needs_rule_context|blocked|clarify",
  "sql": "...",
  "tables_used": ["..."],
  "columns_used": ["..."],
  "estimated_granularity": "aggregated|customer_level|unknown",
  "explanation": "...",
  "safety_notes": ["..."]
}

Pergunta:
{{question}}

Schema catalog:
{{schema_catalog}}

Scenarios:
{{scenarios}}

RAG context:
{{rag_context}}
```

#### Prompt de explicação do resultado

```text
Você é um analista sênior de pricing e risco.

Sua tarefa é transformar o resultado da consulta em explicação executiva em português do Brasil.

Regras:
- Explique primeiro o insight principal.
- Depois, destaque tendências, exceções e implicações.
- Use linguagem clara, objetiva e corporativa.
- Não invente causalidade além do que os dados suportam.
- Se houver limitação do dado, diga explicitamente.
- Se houver regra de negócio relevante recuperada pelo RAG, conecte-a ao achado.
- Se o resultado estiver vazio, diga isso e ofereça hipóteses operacionais.
- Não esconda que houve mascaramento ou agregação.
- Produza:
  1. resumo executivo
  2. leitura analítica
  3. riscos/interpretações
  4. próximos passos sugeridos

Entradas:
Pergunta: {{question}}
SQL: {{sql}}
Resultado: {{result_rows}}
Contexto semântico: {{rag_context}}
Notas de segurança: {{safety_notes}}
```

### Template de README

```markdown
# Agentic Analytics para Pricing

## Visão geral
Plataforma analítica conversacional governada para perguntas de pricing, margem, safra, risco e ROAE.

## Problema de negócio
Descreva o custo atual da análise manual, inconsistência semântica e baixa rastreabilidade.

## Objetivos
- Explicar regras de negócio
- Consultar dados estruturados com segurança
- Gerar respostas auditáveis e relatórios executivos

## Arquitetura
- Frontend: Next.js
- Backend: FastAPI
- Orquestração: LangGraph
- SQL Agent: Text2SQL
- RAG: OpenSearch + Jina Embeddings
- Banco: PostgreSQL / DuckDB
- LLM: Ollama / OpenAI
- Sandbox: execução isolada de código

## Fluxo principal
Pergunta → Guardrail → RAG de regras → Text-to-SQL → Executor seguro → Explicação → Relatório → Auditoria

## Estrutura do repositório
/apps
/packages
/infra
/docs
/tests

## Começando
### Pré-requisitos
### Variáveis de ambiente
### Subir a stack local
### Rodar testes
### Rodar frontend e backend

## Endpoints
- POST /api/v1/ask-analytics
- POST /api/v1/search-rules
- GET /api/v1/health
- GET /api/v1/traces/{trace_id}

## Segurança e governança
Explique whitelist, masking, auditoria e limites de custo.

## Testes
Explique unitários, integração, E2E e segurança.

## Demo
Inclua perguntas de exemplo e fluxo recomendado.

## Roadmap
MVP → workspace persistente → sandbox → skills → automações

## Licença
## Créditos
```

### Template de slides para a banca

| Slide | Título | Pontos-chave |
|---|---|---|
| abertura | Problema e tese | lacuna entre regra de negócio e dado factual; por que copilot analítico |
| contexto | Dor atual | tempo manual, inconsistência, pouca auditabilidade |
| objetivo | O que o produto resolve | pricing, margem, safra, risco, ROAE |
| referências | Base técnica usada | course + text2sql + LangAlpha |
| proposta | Visão do produto | RAG de regras + Text-to-SQL + agente + relatório |
| arquitetura | Diagrama | componentes e fluxo |
| governança | Segurança | whitelist, masking, validação SQL, auditoria |
| fluxo | Jornada de uma pergunta | exemplo concreto de pergunta híbrida |
| dados | Modelo de dados | fatos, catálogo, regras, auditoria |
| métricas | Como medir sucesso | recall, precisão SQL, latência, custo, segurança |
| testes | TDD e evidências | unitário, integração, E2E, segurança |
| demo | Cenário ao vivo | pergunta, fontes, SQL, resposta, relatório |
| roadmap | MVP para produto | fases 1–5 |
| esforço | Plano e cronograma | milestones e horas |
| riscos | O que pode dar errado | mitigação |
| fechamento | Valor para negócio e técnica | ROI, governança, escalabilidade |

### Roteiro de demo

#### Comandos sugeridos

```bash
# infraestrutura
docker compose up --build -d

# backend
uv run uvicorn app.main:app --reload --port 8000

# frontend
pnpm install
pnpm dev

# testes essenciais
pytest -q tests/unit
pytest -q tests/integration
pytest -q tests/security
pytest -q tests/e2e
```

#### Sequência de demo

| Etapa | O que mostrar |
|---|---|
| login/entrada | home do produto e disclaimer de governança |
| pergunta conceitual | “O que significa alto risco nesta política?” |
| resposta conceitual | fontes recuperadas no RAG + política aplicável |
| pergunta analítica | “Qual segmento teve pior margem na última safra?” |
| resposta analítica | SQL executado, tabela e resumo |
| pergunta híbrida | “Explique a regra de alto risco e compare ROAE por safra para alto risco” |
| governança | masking, SQL validator e `trace_id` |
| relatório | download do artefato executivo |
| observabilidade | log/tracing/auditoria persistida |

#### Perguntas de exemplo

```text
O que significa safra nesta base?
Qual foi a margem média por safra no segmento PME?
Quais produtos tiveram pior ROAE na última safra?
Explique a regra de alto risco e compare inadimplência por safra.
Gere um diagnóstico executivo da queda de margem da safra 2026-03.
```

### Checklist de entrega para banca

- [ ] Resumo executivo revisado
- [ ] Diagrama de arquitetura atualizado
- [ ] Fluxo agentic documentado
- [ ] Modelo de dados apresentado
- [ ] Prompts versionados
- [ ] SQL validator demonstrado
- [ ] Masking demonstrado
- [ ] Auditoria e `trace_id` demonstrados
- [ ] Testes unitários executados
- [ ] Testes de integração executados
- [ ] Testes E2E executados
- [ ] Casos de segurança executados
- [ ] Demo script ensaiado
- [ ] Slides finalizados
- [ ] README pronto
- [ ] Riscos e limitações explicitados
- [ ] Itens não especificados declarados
- [ ] Roadmap MVP → produto apresentado

### Pacote de handoff recomendado para implementação por agentes

| Arquivo | Finalidade |
|---|---|
| `AGENTS.md` | instruções de implementação e convenções |
| `ARCHITECTURE.md` | visão técnica e contratos |
| `TASKS.md` | backlog granular com critérios de aceite |
| `PROMPTS.md` | prompts versionados |
| `SCENARIOS.md` | regras de negócio do Text-to-SQL |
| `SECURITY.md` | políticas de validação, masking e auditoria |
| `EVALS.md` | benchmark interno e perguntas ouro |
| `DEMO.md` | roteiro da demonstração |
| `README.md` | onboarding e operação |
| `slides_banca.md` | estrutura da apresentação |

A conclusão estratégica é direta: o projeto mais defensável para banca e mais útil para evolução real não é “um chatbot de dados”, mas um **sistema agentic analytics governado**, em que RAG explica regras, SQL recupera fatos, LangGraph decide o caminho, o sandbox produz artefatos e a trilha de auditoria garante confiança. Esse desenho respeita o que cada repositório faz melhor e reduz o risco de superestimar qualquer abordagem isolada. citeturn11view4turn3view2turn5view0turn6view0turn6view1