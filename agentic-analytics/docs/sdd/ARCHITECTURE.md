# Objetivo
Registrar a arquitetura de referência com foco em rastreabilidade e governança para desenvolvimento guiado por especificação.

## Diagrama de Alto Nível
```mermaid
flowchart LR
  subgraph Frontend
    FE[Next.js App]
  end

  subgraph Backend
    API[FastAPI API]
    WS[Workspace Endpoints]
    ASK[Ask Analytics]
    SSE[SSE Stream]
  end

  subgraph Agentic
    GR[Guardrail]
    SUP[Supervisor]
    SQL[Text2SQL Agent]
    RAG[RAG Agent]
  end

  subgraph Data
    PG[(PostgreSQL)]
    DK[(DuckDB)]
    RS[(Redis)]
    OS[(OpenSearch)]
  end

  FE --> API
  API --> WS
  API --> ASK
  ASK --> GR
  GR --> SUP
  SUP --> SQL
  SUP --> RAG
  SQL --> DK
  SQL --> PG
  RAG --> OS
  API --> SSE
  SSE --> RS
```

## Legenda
- Frontend consome endpoints REST e canal SSE.
- Backend injeta `trace_id` por request e o propaga no payload JSON.
- Orquestração usa guardrails e roteamento por intenção.
- Camadas de dados permanecem protegidas por validações de segurança e políticas de mascaramento.
