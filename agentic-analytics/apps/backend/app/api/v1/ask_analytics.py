"""
POST /api/v1/ask-analytics — endpoint principal do sistema agentic.
SSE /api/v1/ask-analytics/stream — endpoint de streaming com Redis.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Request, Header, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.graph import run_analytics
from app.tracing.audit import persist_audit_log
from app.config import settings
from app.api.v1.workspaces import get_workspace, persist_thread_message
from app.api.v1.response_envelope import envelope_payload

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


@router.post("/ask-analytics")
async def ask_analytics(
    body: AskRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Endpoint principal síncrono — executa o fluxo agentic completo.
    """
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    start_ms = int(datetime.utcnow().timestamp() * 1000)

    config = {}
    if body.model:
        config["model"] = body.model
    if body.top_k:
        config["top_k"] = body.top_k

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

    from app.services.security import PIIMasker
    
    # Mascara PII antes de persistir e retornar
    masked_question = PIIMasker.mask_text(body.question)
    result = PIIMasker.mask_dict(result)

    background_tasks.add_task(
        persist_audit_log,
        trace_id=trace_id,
        question=masked_question,
        routed_path=result.get("routed_path", "unknown"),
        sql_final=result.get("sql"),
        status="success",
        latency_ms=latency_ms,
        masked_fields=result.get("masked_fields", []),
    )

    if body.thread_id:
        background_tasks.add_task(
            persist_thread_message,
            thread_id=body.thread_id,
            role="user",
            content=masked_question,
        )
        background_tasks.add_task(
            persist_thread_message,
            thread_id=body.thread_id,
            role="assistant",
            content=result.get("answer", ""),
            metadata={
                "trace_id": trace_id,
                "routed_path": result.get("routed_path"),
                "sql": result.get("sql"),
                "sql_result": result.get("sql_result"),
                "sources": result.get("sources"),
                "masked_fields": result.get("masked_fields"),
                "artifacts": result.get("artifacts"),
                "sandbox_result": result.get("sandbox_result"),
                "specialist_messages": result.get("specialist_messages"),
            },
        )

    response_data = AskResponse(
        trace_id=trace_id,
        question=masked_question,
        answer=result.get("answer", ""),
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
    return envelope_payload(
        data=response_data.model_dump(),
        request=request,
        trace_id=trace_id,
    )


# ─── SSE Streaming (Fase 2.5) ────────────────────────────────────────────────

async def background_run_stream(body: AskRequest, trace_id: str):
    """Executa o grafo em background, emitindo eventos para o Redis Stream."""
    start_ms = int(datetime.utcnow().timestamp() * 1000)
    config = {}
    if body.model:
        config["model"] = body.model
    if body.top_k:
        config["top_k"] = body.top_k

    if body.workspace_id:
        ws = get_workspace(body.workspace_id)
        if ws and ws.agent_md:
            config["agent_context"] = ws.agent_md

    from app.services.security import PIIMasker
    masked_question = PIIMasker.mask_text(body.question)

    # Persiste a mensagem de input do usuário antes de rodar
    if body.thread_id:
        persist_thread_message(body.thread_id, "user", masked_question)

    try:
        from app.agent.graph import run_analytics_stream
        await run_analytics_stream(body.question, trace_id, config)

        # Após finalizar, obtém o payload final de 'done' para persistir e auditar
        from app.services.redis_client import redis_mgr
        events = await redis_mgr.get_events_from(trace_id, "0-0")
        done_event = next((e for e in events if e["type"] == "done"), None)

        if done_event:
            data = done_event["data"]
            data = PIIMasker.mask_dict(data)
            
            # Auditoria
            latency_ms = int(datetime.utcnow().timestamp() * 1000) - start_ms
            persist_audit_log(
                trace_id=trace_id,
                question=masked_question,
                routed_path=data.get("routed_path", "unknown"),
                sql_final=data.get("sql"),
                status="success",
                latency_ms=latency_ms,
                masked_fields=data.get("masked_fields", []),
            )

            # Persiste resposta do assistente no histórico
            if body.thread_id:
                persist_thread_message(
                    body.thread_id,
                    "assistant",
                    data.get("answer", ""),
                    metadata={
                        "trace_id": trace_id,
                        "routed_path": data.get("routed_path"),
                        "sql": data.get("sql"),
                        "sql_result": data.get("sql_result"),
                        "sources": data.get("sources"),
                        "masked_fields": data.get("masked_fields"),
                        "artifacts": data.get("artifacts"),
                        "sandbox_result": data.get("sandbox_result"),
                        "specialist_messages": data.get("specialist_messages"),
                    },
                )
                # Persiste artefatos gerados
                artifacts = data.get("artifacts", [])
                if artifacts:
                    from app.db.session import SessionLocal
                    from app.models.workspace import Artifact
                    with SessionLocal() as db_session:
                        for art in artifacts:
                            db_art = Artifact(
                                thread_id=body.thread_id,
                                tipo=art.get("tipo", "markdown"),
                                conteudo=art.get("conteudo", ""),
                                url=art.get("url"),
                                meta_data=art.get("metadata", {}),
                            )
                            db_session.add(db_art)
                        db_session.commit()
    except Exception as e:
        # Se der erro, auditoria de falha
        latency_ms = int(datetime.utcnow().timestamp() * 1000) - start_ms
        persist_audit_log(
            trace_id=trace_id,
            question=body.question,
            routed_path="error",
            sql_final=None,
            status="failed",
            latency_ms=latency_ms,
            masked_fields=[],
        )


@router.post("/ask-analytics/stream")
async def start_analytics_stream(
    body: AskRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Inicia processamento do agente em background e retorna o trace_id do stream."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    background_tasks.add_task(background_run_stream, body, trace_id)
    return envelope_payload(
        data={"trace_id": trace_id},
        request=request,
        trace_id=trace_id,
    )


@router.get("/ask-analytics/stream/{trace_id}")
async def get_stream(
    trace_id: str,
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    last_event_id_query: Optional[str] = Query(None, alias="last_event_id"),
):
    """
    Retorna canal SSE (Server-Sent Events) dos eventos do trace_id.
    Suporta recuperação/replay automático via Header Last-Event-ID ou Query last_event_id.
    """
    event_id = last_event_id or last_event_id_query or "0-0"

    async def event_generator():
        nonlocal event_id
        from app.services.redis_client import redis_mgr

        # 1. Recupera eventos anteriores do replay buffer do Redis (se houver)
        replayed = await redis_mgr.get_events_from(trace_id, event_id)
        for ev in replayed:
            event_id = ev["id"]
            yield f"id: {ev['id']}\nevent: {ev['type']}\ndata: {json.dumps(ev['data'])}\n\n"
            if ev["type"] in ("done", "error"):
                return

        # 2. Assina novos eventos bloqueando no Redis Stream
        while True:
            new_events = await redis_mgr.read_new_events(trace_id, event_id, block_ms=2000)
            for ev in new_events:
                event_id = ev["id"]
                yield f"id: {ev['id']}\nevent: {ev['type']}\ndata: {json.dumps(ev['data'])}\n\n"
                if ev["type"] in ("done", "error"):
                    return
            await asyncio.sleep(0.1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
