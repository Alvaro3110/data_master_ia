"""
Workspace Models — Fase 2.5: Entidades de Workspace, Thread e Artifact persistidas em PostgreSQL.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Workspace ────────────────────────────────────────────────────────────────


class Workspace(Base):
    """
    Sessão de análise persistente.
    Mantém contexto de longo prazo via agent_md (instruções customizadas).
    """
    __tablename__ = "workspaces"

    id = Column(String(50), primary_key=True, default=_uuid)
    nome = Column(String(200), nullable=False)
    user_id = Column(String(100), nullable=False)
    agent_md = Column(Text, nullable=True, default="")
    criado_em = Column(DateTime, nullable=False, default=_now)
    atualizado_em = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    threads = relationship("Thread", back_populates="workspace", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = _uuid()
        if not self.criado_em:
            self.criado_em = _now()
        if not self.atualizado_em:
            self.atualizado_em = _now()
        if self.agent_md is None:
            self.agent_md = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "user_id": self.user_id,
            "agent_md": self.agent_md or "",
            "criado_em": self.criado_em.isoformat() if isinstance(self.criado_em, datetime) else self.criado_em,
            "atualizado_em": self.atualizado_em.isoformat() if isinstance(self.atualizado_em, datetime) else self.atualizado_em,
        }


# ── Thread ───────────────────────────────────────────────────────────────────


class Thread(Base):
    """
    Conversa dentro de um Workspace.
    Armazena o histórico de mensagens (user/assistant) e o status.
    """
    __tablename__ = "threads"

    id = Column(String(50), primary_key=True, default=_uuid)
    workspace_id = Column(String(50), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active | archived | failed
    mensagens = Column(JSON, nullable=False, default=list)
    criado_em = Column(DateTime, nullable=False, default=_now)
    atualizado_em = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    workspace = relationship("Workspace", back_populates="threads")
    artifacts = relationship("Artifact", back_populates="thread", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = _uuid()
        if not self.criado_em:
            self.criado_em = _now()
        if not self.atualizado_em:
            self.atualizado_em = _now()
        if self.mensagens is None:
            self.mensagens = []
        if not self.status:
            self.status = "active"

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """Adiciona uma mensagem ao histórico da thread."""
        msgs = list(self.mensagens or [])
        msgs.append({
            "role": role,
            "content": content,
            "timestamp": _now().isoformat(),
            "metadata": metadata or {},
        })
        self.mensagens = msgs
        self.atualizado_em = _now()

    def get_messages(self) -> list[dict]:
        """Retorna o histórico de mensagens."""
        return self.mensagens or []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "titulo": self.titulo,
            "status": self.status,
            "mensagens": self.mensagens or [],
            "criado_em": self.criado_em.isoformat() if isinstance(self.criado_em, datetime) else self.criado_em,
            "atualizado_em": self.atualizado_em.isoformat() if isinstance(self.atualizado_em, datetime) else self.atualizado_em,
        }


# ── Artifact ─────────────────────────────────────────────────────────────────


class Artifact(Base):
    """
    Artefato gerado por uma Thread (relatório, gráfico, tabela, etc.).
    Persistido no banco e disponibilizado para download no frontend.
    """
    __tablename__ = "artifacts"

    id = Column(String(50), primary_key=True, default=_uuid)
    thread_id = Column(String(50), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(50), nullable=False)  # "markdown" | "pdf" | "xlsx" | "png" | "json" | "html"
    conteudo = Column(Text, nullable=False)
    url = Column(String(500), nullable=True)
    meta_data = Column("metadata", JSON, nullable=False, default=dict)
    criado_em = Column(DateTime, nullable=False, default=_now)

    thread = relationship("Thread", back_populates="artifacts")

    def __init__(self, **kwargs):
        # Mapeia parâmetro metadata para meta_data se fornecido
        metadata_val = kwargs.pop("metadata", None)
        super().__init__(**kwargs)
        if not self.id:
            self.id = _uuid()
        if not self.criado_em:
            self.criado_em = _now()
        if metadata_val is not None:
            self.meta_data = metadata_val
        elif self.meta_data is None:
            self.meta_data = {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "tipo": self.tipo,
            "conteudo": self.conteudo[:500],  # preview truncado
            "url": self.url,
            "metadata": self.meta_data or {},
            "criado_em": self.criado_em.isoformat() if isinstance(self.criado_em, datetime) else self.criado_em,
        }
