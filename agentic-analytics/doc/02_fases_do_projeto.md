# Evolução do Projeto: Linha do Tempo e Fases

O projeto foi meticulosamente dividido em fases incrementais de complexidade. Abaixo está a evolução cronológica:

## Fase 1: RAG e SQL Governados de Verdade
- **Objetivo:** Estabelecer a base fundamental para os dois motores de geração de conhecimento do banco de dados (RAG e Text2SQL).
- **Entregas:**
  - `SQL Validator`: Criação do interpretador AST (Abstract Syntax Tree) usando `sqlglot` para validar estaticamente qualquer SQL gerado pela IA antes de rodar contra o banco, prevenindo manipulações danosas.
  - `RagAgent`: Implementação de busca Híbrida local mockada.
  - `Text2SQL Agent`: Gerador estruturado que consome metadados e retorna queries otimizadas.
- **TDD:** Testes rigorosos na camada de validação e restrição de schemas e comandos proibidos (ex: `DROP`, `UPDATE`).

## Fase 2: Workspaces e Persistência
- **Objetivo:** Fazer o sistema ter "memória" multi-usuário e multi-sessão, algo fundamental para interfaces de longo prazo.
- **Entregas:**
  - Base SQLite com mapeamento de `Workspace`, `Thread` e `Artifact`.
  - Backend (FastAPI): Rotas de CRUD para listagem de sessões.
  - Frontend (Next.js): Criação da Sidebar (menu lateral) gerenciando diferentes threads de contexto do usuário de forma fluida.

## Fase 3: Sandbox e PTC (Programmatic Tool Calling)
- **Objetivo:** Permitir que o sistema analítico "rode" código Python internamente para elaborar gráficos, cálculos complexos e manipulação de tabelas pandas.
- **Entregas:**
  - **SandboxExecutor:** Uma feature que executa trechos de Python em um subprocesso capado (sem acesso a env vars sensíveis e com timeout).
  - **ReportGenerator / ArtifactViewer:** O sistema deixa de responder com texto simples e passa a gerar *Artefatos em Markdown* e tabelas estruturadas renderizadas visualmente na interface React.

## Fase 4: Swarm (Supervisor + Especialistas)
- **Objetivo:** Desacoplar o grafo linear (Perguntar -> RAG -> SQL -> Resposta) para uma estrutura distribuída e paralela de especialistas.
- **Entregas:**
  - Criação do **Orchestrator** (Supervisor) que avalia a intenção da query e aciona dinamicamente as "skills".
  - Refatoração dos agentes para operarem como subagentes isolados (**DataAgent** e **RiskAgent**).
  - Implementação do **Debate Swarm** na UI (TracePanel), permitindo ao usuário auditar o que cada subagente avaliou.

## Fase 5: Avaliação Contínua e Dataset (Evals)
- **Objetivo:** Criar um ambiente para garantir a estabilidade contra "regressões de LLM", permitindo rodar *red teaming* e *LLM-as-a-judge*.
- **Entregas:**
  - Utilitários locais `evaluate_relevance` e `evaluate_sql_accuracy`.
  - Script autônomo `scripts/evaluate_langsmith.py` que roda testes em lote simulando um pipeline CI/CD de Machine Learning.
