"""
Workspace Models — Fase 2: Entidades de Workspace, Thread e Artifact.
Modelos em memória (dataclasses) para funcionar sem banco durante os testes.
Em produção, esses models são substituídos por SQLAlchemy ORM mapeados no banco.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Workspace ────────────────────────────────────────────────────────────────

@dataclass
class Workspace:
    """
    Sessão de análise persistente.
    Mantém contexto de longo prazo via agent_md (instruções customizadas).
    """
    nome: str
    user_id: str
    id: str = field(default_factory=_uuid)
    agent_md: Optional[str] = ""
    criado_em: datetime = field(default_factory=_now)
    atualizado_em: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "user_id": self.user_id,
            "agent_md": self.agent_md,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
        }


# ── Thread ───────────────────────────────────────────────────────────────────

@dataclass
class Thread:
    """
    Conversa dentro de um Workspace.
    Armazena o histórico de mensagens (user/assistant) e o status.
    """
    workspace_id: str
    titulo: str
    id: str = field(default_factory=_uuid)
    status: str = "active"  # active | archived | failed
    mensagens: list[dict] = field(default_factory=list)
    criado_em: datetime = field(default_factory=_now)
    atualizado_em: datetime = field(default_factory=_now)

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """Adiciona uma mensagem ao histórico da thread."""
        self.mensagens.append({
            "role": role,
            "content": content,
            "timestamp": _now().isoformat(),
            "metadata": metadata or {},
        })
        self.atualizado_em = _now()

    def get_messages(self) -> list[dict]:
        """Retorna o histórico de mensagens."""
        return self.mensagens

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "titulo": self.titulo,
            "status": self.status,
            "mensagens": self.mensagens,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
        }


# ── Artifact ─────────────────────────────────────────────────────────────────

ARTIFACT_TIPOS = {"markdown", "pdf", "xlsx", "png", "json", "html"}


@dataclass
class Artifact:
    """
    Artefato gerado por uma Thread (relatório, gráfico, tabela, etc.).
    Persistido no banco e disponibilizado para download no frontend.
    """
    thread_id: str
    tipo: str  # "markdown" | "pdf" | "xlsx" | "png" | "json"
    conteudo: str
    id: str = field(default_factory=_uuid)
    url: Optional[str] = None  # URL pública para download
    metadata: dict = field(default_factory=dict)
    criado_em: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "tipo": self.tipo,
            "conteudo": self.conteudo[:500],  # preview truncado
            "url": self.url,
            "metadata": self.metadata,
            "criado_em": self.criado_em.isoformat(),
        }
