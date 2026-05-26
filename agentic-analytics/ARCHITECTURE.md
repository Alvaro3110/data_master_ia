# 🏗️ Agentic Analytics — Arquitetura de Sistema

Este documento detalha o desenho técnico da plataforma **Agentic Analytics**, focada em consultas seguras e governadas para Data Warehousing financeiro.

---

## 1. Topologia Macro

O sistema segue uma abordagem *Headless Agent* onde um backend em FastAPI expõe rotas conversacionais governadas para um Frontend Next.js.

```mermaid
graph LR
    subgraph UI [Frontend Layer]
        NextJS[Next.js 14 App Router]
        Chat[ChatPanel UI]
        Trace[TracePanel UI]
        NextJS --- Chat
        NextJS --- Trace
    end

    subgraph API [Backend API - FastAPI]
        AskEndpoint[POST /ask-analytics]
        AuditEndpoint[GET /traces]
    end

    subgraph Core [Agentic Engine - LangGraph]
        Guard[Guardrail Validator]
        RAG[RAG Agent]
        SQL[Text2SQL Agent]
        Ollama[Ollama llama3.2]
    end

    subgraph Data [Data Layer]
        DW[(PostgreSQL / DuckDB)]
        Vect[(OpenSearch / Jina)]
        AuditLog[(Audit Log)]
    end

    Chat -->|Question| AskEndpoint
    AskEndpoint --> Guard
    Guard --> RAG & SQL
    RAG --> Vect
    SQL --> DW
    RAG & SQL --> Ollama
    Ollama --> AuditLog
    AuditLog --> AskEndpoint
    AskEndpoint --> Trace
```

---

## 2. Padrão de Design LangGraph (Week 7 Pattern)

O coração do sistema utiliza um design focado em recuperação e robustez (Resilience by Design). 

1. **Routing:** Todo o tráfego é pontuado por um *Guardrail* (score de 0 a 100).
2. **Retrieve:** Documentos e queries SQL são tentados.
3. **Grade / Rewrite:** O `SQLValidator` funciona como *grader*. Se uma query é bloqueada ou falha na execução, a LLM entra em um loop para *Reescrever a Query* (`rewrite_query`).
4. **Answer:** O compilado de logs analíticos é traduzido em insight narrativo humano.

```mermaid
stateDiagram-v2
    [*] --> Guardrail: User Prompt
    Guardrail --> OutOfScope: Score < 60
    Guardrail --> Router: Score >= 60
    
    Router --> RAG: Conceptual/Hybrid
    Router --> Text2SQL: Analytics
    
    RAG --> Text2SQL: Hybrid
    RAG --> AnswerGenerator: Conceptual
    
    state Text2SQL {
        GenerateSQL --> ValidateSQL
        ValidateSQL --> ExecuteSQL: Valid
        ValidateSQL --> Blocked: Injection/FullScan
    }
    
    ExecuteSQL --> AnswerGenerator: Success
    ExecuteSQL --> RewriteQuery: Fail (Empty/Error)
    Blocked --> RewriteQuery
    
    RewriteQuery --> RAG: Retry
    
    AnswerGenerator --> [*]
```

---

## 3. Data Flow & Security (Zero Trust Model)

A segurança em arquiteturas Agentic/Text-to-SQL é uma prioridade crítica. Este sistema implementa uma pipeline *Zero Trust* em 3 estágios.

```mermaid
sequenceDiagram
    participant User
    participant LLM Agent
    participant SQL Validator
    participant Data Warehouse
    participant Data Masker

    User->>LLM Agent: Qual cliente teve pior margem?
    LLM Agent->>SQL Validator: Gerou SQL: SELECT nome_cliente, margem FROM ...
    
    Note over SQL Validator: AST Parsing<br/>Bloqueia DELETE/UPDATE<br/>Checa LIMIT
    
    SQL Validator->>Data Warehouse: Envia SQL validado
    Data Warehouse-->>Data Masker: Retorna raw rows
    
    Note over Data Masker: SHA-256 Hash em `nome_cliente`<br/>(Regra PII)
    
    Data Masker-->>LLM Agent: Rows: [{"nome_cliente": "***9a4", "margem": -2.1}]
    LLM Agent-->>User: "O cliente ***9a4 teve a pior margem (-2.1)"
```

### Regras do SQL Validator:
- **Parse Árvore (AST):** O validator utiliza análise léxica em vez de Regex para detectar injeção nas cláusulas de `WHERE`, `JOIN` ou comentários obscurecidos.
- **DML Bloqueado:** `INSERT`, `UPDATE`, `DELETE`, `MERGE` são vetados instantaneamente.
- **Cardinality Budgeting:** Queries que atingem tabelas gigantes (ex: `fact_pricing_snapshot`) obrigatoriamente precisam de um teto estrito na devolução (`LIMIT`).

---

## 4. Estrutura de Componentes da UI (Next.js)

O painel de chat não é apenas uma caixa de texto. O modelo cognitivo do usuário se apoia na transparência dos Agentes através de *Componentes Plugáveis*.

```mermaid
classDiagram
    class ChatPanel {
        +State[] messages
        +sendMessage(query)
    }
    class MessageBubble {
        +Role: User/Assistant
        +MarkdownContent
    }
    class SQLViewer {
        +String SQL
        +ColorizeSyntax()
        +CopyClipboard()
    }
    class TracePanel {
        +String TraceID
        +Int Latency
        +Array ReasoningSteps
        +ToggleVisibility()
    }
    class SourcesPanel {
        +Array Documents
        +RenderReferences()
    }

    ChatPanel *-- MessageBubble
    MessageBubble *-- SQLViewer: Renderiza Condicional
    MessageBubble *-- TracePanel: Renderiza Condicional
    MessageBubble *-- SourcesPanel: Renderiza Condicional
```

A interface foi projetada em **Dark Mode Premium**, focando na legibilidade de código (`SQLViewer` utiliza tipografia mono-espaçada nativa e realce sintático iterado de tokens como `SELECT` e `GROUP BY`). O `TracePanel` garante que o usuário entenda precisamente **como** e **por que** a IA tomou certas decisões.
