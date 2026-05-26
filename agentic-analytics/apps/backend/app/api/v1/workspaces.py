"""
Workspace API — Fase 2: CRUD de Workspaces e Threads.
Endpoints:
  POST   /api/v1/workspaces               — criar workspace
  GET    /api/v1/workspaces               — listar por user_id
  GET    /api/v1/workspaces/{id}/threads  — listar threads
  POST   /api/v1/workspaces/{id}/threads  — criar thread
  PUT    /api/v1/workspaces/{id}/agent-md — atualizar agent.md
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.models.workspace import Workspace, Thread

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])

# ── Armazenamento em memória (substituído por PostgreSQL em produção) ─────────
_workspaces: dict[str, Workspace] = {}
_threads: dict[str, Thread] = {}


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
async def create_workspace(body: CreateWorkspaceRequest):
    """Cria um novo workspace de análise."""
    ws = Workspace(nome=body.nome, user_id=body.user_id, agent_md=body.agent_md)
    _workspaces[ws.id] = ws
    return ws.to_dict()


@router.get("")
async def list_workspaces(user_id: str = Query(..., description="ID do usuário")):
    """Lista todos os workspaces de um usuário."""
    return [ws.to_dict() for ws in _workspaces.values() if ws.user_id == user_id]


@router.get("/{workspace_id}/threads")
async def list_threads(workspace_id: str):
    """Lista threads de um workspace."""
    if workspace_id not in _workspaces:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' não encontrado.")
    return [t.to_dict() for t in _threads.values() if t.workspace_id == workspace_id]


@router.post("/{workspace_id}/threads", status_code=201)
async def create_thread(workspace_id: str, body: CreateThreadRequest):
    """Cria uma nova thread dentro de um workspace."""
    if workspace_id not in _workspaces:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' não encontrado.")
    thread = Thread(workspace_id=workspace_id, titulo=body.titulo)
    _threads[thread.id] = thread
    return thread.to_dict()


@router.put("/{workspace_id}/agent-md")
async def update_agent_md(workspace_id: str, body: UpdateAgentMdRequest):
    """Atualiza o agent.md (instruções customizadas) do workspace."""
    if workspace_id not in _workspaces:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' não encontrado.")
    ws = _workspaces[workspace_id]
    ws.agent_md = body.agent_md
    return ws.to_dict()


def get_workspace(workspace_id: str) -> Optional[Workspace]:
    """Helper para outros módulos consultarem o workspace ativo."""
    return _workspaces.get(workspace_id)


def persist_thread_message(thread_id: str, role: str, content: str, metadata: dict = None) -> None:
    """Persiste uma mensagem em uma thread existente."""
    if thread_id in _threads:
        _threads[thread_id].add_message(role=role, content=content, metadata=metadata or {})
