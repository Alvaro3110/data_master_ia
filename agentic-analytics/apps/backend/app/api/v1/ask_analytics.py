"""
POST /api/v1/ask-analytics — endpoint principal do sistema agentic.
Padrão: Week7 /ask-agentic + campos de pricing/risco/ROAE.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.graph import run_analytics
from app.tracing.audit import persist_audit_log
from app.config import settings
from app.api.v1.workspaces import get_workspace, persist_thread_message

router = APIRouter()


class AskRequest(BaseModel):
    question: str
    workspace_id: str | None = None  # Fase 2: workspace opcional
    thread_id: str | None = None     # Fase 2: thread opcional
    mode: str = "auto"  # "auto" | "rag" | "sql"
    top_k: int = 3
    model: str | None = None


class AskResponse(BaseModel):
    trace_id: str
    question: str
    answer: str
    routed_path: str
    reasoning_steps: list[str]
    retrieval_attempts: int
    rewritten_query: str | None
    sources: list[str]
    sql: str | None
    sql_result: list[dict] | None
    masked_fields: list[str]
    artifacts: list[dict] = []
    sandbox_result: dict | None = None
    specialist_messages: list[dict] = []
    latency_ms: int
    status: str = "success"


@router.post("/ask-analytics", response_model=AskResponse)
async def ask_analytics(
    body: AskRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Endpoint principal — executa o fluxo agentic completo.

    Fluxo: guardrail → router → [RAG | Text2SQL | híbrido] → resposta → auditoria
    """
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    start_ms = int(datetime.utcnow().timestamp() * 1000)

    config = {}
    if body.model:
        config["model"] = body.model
    if body.top_k:
        config["top_k"] = body.top_k

    # Injeta contexto do workspace (agent_md) se fornecido
    agent_context = ""
    if body.workspace_id:
        ws = get_workspace(body.workspace_id)
        if ws and ws.agent_md:
            agent_context = ws.agent_md
            config["agent_context"] = agent_context

    result = await run_analytics(
        question=body.question,
        trace_id=trace_id,
        config=config,
    )

    latency_ms = int(datetime.utcnow().timestamp() * 1000) - start_ms

    # Auditoria em background (não bloqueia resposta)
    background_tasks.add_task(
        persist_audit_log,
        trace_id=trace_id,
        question=body.question,
        routed_path=result.get("routed_path", "unknown"),
        sql_final=result.get("sql"),
        status="success",
        latency_ms=latency_ms,
        masked_fields=result.get("masked_fields", []),
    )

    # Persiste mensagens na thread do workspace (Fase 2)
    if body.thread_id:
        background_tasks.add_task(
            persist_thread_message,
            thread_id=body.thread_id,
            role="user",
            content=body.question,
        )
        background_tasks.add_task(
            persist_thread_message,
            thread_id=body.thread_id,
            role="assistant",
            content=result.get("answer", ""),
            metadata={"trace_id": trace_id, "routed_path": result.get("routed_path")},
        )

    return AskResponse(
        trace_id=trace_id,
        question=body.question,
        answer=result["answer"],
        routed_path=result.get("routed_path", "unknown"),
        reasoning_steps=result.get("reasoning_steps", []),
        retrieval_attempts=result.get("retrieval_attempts", 0),
        rewritten_query=result.get("rewritten_query"),
        sources=result.get("sources", []),
        sql=result.get("sql"),
        sql_result=result.get("sql_result"),
        masked_fields=result.get("masked_fields", []),
        artifacts=result.get("artifacts", []),
        sandbox_result=result.get("sandbox_result"),
        specialist_messages=result.get("specialist_messages", []),
        latency_ms=latency_ms,
        status="success",
    )
