"""
Workspace API — Fase 2.5: CRUD de Workspaces e Threads persistidos em banco de dados.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.models.workspace import Workspace, Thread

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


# ── Armazenamento Persistente com compatibilidade de reset ────────────────────
class EphemeralWorkspaceDB:
    def reset(self):
        """Reseta o banco de dados. Útil para testes TDD determinísticos."""
        from app.db.session import engine, Base
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)


db = EphemeralWorkspaceDB()


# ── Schemas Pydantic ─────────────────────────────────────────────────────────

class CreateWorkspaceRequest(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    user_id: str = Field(..., min_length=1)
    agent_md: Optional[str] = ""


class CreateThreadRequest(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)


class UpdateAgentMdRequest(BaseModel):
    agent_md: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_workspace(body: CreateWorkspaceRequest, db_session: Session = Depends(get_db)):
    """Cria um novo workspace de análise."""
    ws = Workspace(nome=body.nome, user_id=body.user_id, agent_md=body.agent_md)
    db_session.add(ws)
    db_session.commit()
    db_session.refresh(ws)
    return ws.to_dict()


@router.get("")
async def list_workspaces(
    user_id: str = Query(..., description="ID do usuário"),
    db_session: Session = Depends(get_db),
):
    """Lista todos os workspaces de um usuário."""
    workspaces = db_session.query(Workspace).filter(Workspace.user_id == user_id).all()
    return [ws.to_dict() for ws in workspaces]


@router.get("/{workspace_id}/threads")
async def list_threads(workspace_id: str, db_session: Session = Depends(get_db)):
    """Lista threads de um workspace."""
    ws = db_session.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' não encontrado.")
    threads = db_session.query(Thread).filter(Thread.workspace_id == workspace_id).all()
    return [t.to_dict() for t in threads]


@router.post("/{workspace_id}/threads", status_code=201)
async def create_thread(
    workspace_id: str,
    body: CreateThreadRequest,
    db_session: Session = Depends(get_db),
):
    """Cria uma nova thread dentro de um workspace."""
    ws = db_session.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' não encontrado.")
    thread = Thread(workspace_id=workspace_id, titulo=body.titulo)
    db_session.add(thread)
    db_session.commit()
    db_session.refresh(thread)
    return thread.to_dict()


@router.put("/{workspace_id}/agent-md")
async def update_agent_md(
    workspace_id: str,
    body: UpdateAgentMdRequest,
    db_session: Session = Depends(get_db),
):
    """Atualiza o agent.md (instruções customizadas) do workspace."""
    ws = db_session.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' não encontrado.")
    ws.agent_md = body.agent_md
    db_session.commit()
    db_session.refresh(ws)
    return ws.to_dict()


def get_workspace(workspace_id: str) -> Optional[Workspace]:
    """Helper para outros módulos consultarem o workspace ativo."""
    with SessionLocal() as db_session:
        return db_session.query(Workspace).filter(Workspace.id == workspace_id).first()


def persist_thread_message(
    thread_id: str, role: str, content: str, metadata: dict = None
) -> None:
    """Persiste uma mensagem em uma thread existente."""
    with SessionLocal() as db_session:
        thread = db_session.query(Thread).filter(Thread.id == thread_id).first()
        if thread:
            thread.add_message(role=role, content=content, metadata=metadata)
            db_session.commit()
