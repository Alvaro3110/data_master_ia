# Objetivo
Documentar o fluxo técnico completo da plataforma para reduzir ambiguidade entre camadas e orientar evolução controlada.

## Diagrama de Alto Nível
```mermaid
flowchart LR
  subgraph Frontend
    FE[Next.js App]
    UI1[WorkspaceSidebar]
    UI2[ChatPanel]
  end

  subgraph API
    BE[FastAPI API]
    MW[Trace Middleware]
    WS[Workspaces API]
    ASK[POST /ask-analytics]
    STREAM_START[POST /ask-analytics/stream]
    STREAM_GET[GET /ask-analytics/stream/{trace_id}]
  end

  subgraph Agentic
    GR[Guardrail]
    SUP[Supervisor]
    SQLA[SQL Agent]
    RAGA[RAG Agent]
  end

  subgraph Data
    PG[(PostgreSQL)]
    DK[(DuckDB)]
    OS[(OpenSearch)]
    RD[(Redis Streams)]
  end

  FE --> BE
  UI1 --> WS
  UI2 --> ASK
  UI2 --> STREAM_START
  UI2 --> STREAM_GET

  BE --> MW
  MW --> WS
  MW --> ASK
  MW --> STREAM_START

  ASK --> GR
  GR --> SUP
  SUP --> SQLA
  SUP --> RAGA

  SQLA --> DK
  SQLA --> PG
  RAGA --> OS

  STREAM_START --> RD
  STREAM_GET --> RD
```

## Fluxo de Resposta
- Endpoints HTTP JSON respondem no envelope `{trace_id, data}`.
- `trace_id` é propagado em header `X-Trace-ID` e no corpo.
- SSE mantém stream textual, com evento `done` contendo `trace_id` para correlação final.

## Fronteiras de Segurança
- SQL só executa após validação AST.
- Dados sensíveis passam por mascaramento antes de retorno e auditoria.
- CORS restrito por origem controlada.

## Pontos de Escalabilidade
- Redis stream suporta replay por `last_event_id`.
- Especialistas LangGraph podem ser adicionados sem quebrar contrato HTTP.
- Contratos de API e dados são versionados em `docs/sdd`.
