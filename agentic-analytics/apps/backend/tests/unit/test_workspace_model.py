"""
TDD — Fase 2: Workspace Model (SQLAlchemy).
Testa que:
- Workspace pode ser criado com nome e user_id
- Thread pertence a um Workspace e tem histórico de mensagens
- Artifact pertence a uma Thread e tem tipo, conteúdo e url
- Modelos têm campos obrigatórios e defaults corretos
- Serialização para dict funciona
"""
import pytest
from datetime import datetime, UTC
from app.models.workspace import Workspace, Thread, Artifact


class TestWorkspaceModel:
    def test_cria_workspace_com_campos_obrigatorios(self):
        ws = Workspace(nome="Análise Safra 2026-03", user_id="user-123")
        assert ws.nome == "Análise Safra 2026-03"
        assert ws.user_id == "user-123"
        assert ws.id is not None  # UUID gerado automaticamente
        assert ws.criado_em is not None

    def test_workspace_tem_agent_md_vazio_por_default(self):
        ws = Workspace(nome="Teste", user_id="u1")
        assert ws.agent_md == "" or ws.agent_md is None

    def test_workspace_pode_ter_agent_md_personalizado(self):
        ws = Workspace(
            nome="Pricing PME",
            user_id="u1",
            agent_md="Você é especialista em PME. Sempre filtre por segmento=PME.",
        )
        assert "PME" in ws.agent_md

    def test_workspace_to_dict(self):
        ws = Workspace(nome="Demo", user_id="u1")
        d = ws.to_dict()
        assert "id" in d
        assert "nome" in d
        assert "user_id" in d
        assert "criado_em" in d


class TestThreadModel:
    def test_cria_thread_pertencendo_a_workspace(self):
        ws = Workspace(nome="Demo", user_id="u1")
        thread = Thread(workspace_id=ws.id, titulo="Análise de Margem")
        assert thread.workspace_id == ws.id
        assert thread.titulo == "Análise de Margem"
        assert thread.id is not None
        assert thread.status == "active"

    def test_thread_mensagens_comecam_vazias(self):
        thread = Thread(workspace_id="ws-1", titulo="T1")
        assert thread.mensagens == [] or thread.mensagens is None

    def test_thread_adiciona_mensagem(self):
        thread = Thread(workspace_id="ws-1", titulo="T1")
        thread.add_message(role="user", content="Qual a margem?")
        thread.add_message(role="assistant", content="A margem foi 4.2%.")
        assert len(thread.get_messages()) == 2
        assert thread.get_messages()[0]["role"] == "user"

    def test_thread_to_dict(self):
        thread = Thread(workspace_id="ws-1", titulo="T1")
        d = thread.to_dict()
        assert "id" in d
        assert "workspace_id" in d
        assert "titulo" in d
        assert "status" in d


class TestArtifactModel:
    def test_cria_artifact_pertencendo_a_thread(self):
        artifact = Artifact(
            thread_id="thread-1",
            tipo="markdown",
            conteudo="# Relatório\n\nResultado da análise...",
        )
        assert artifact.thread_id == "thread-1"
        assert artifact.tipo == "markdown"
        assert "Relatório" in artifact.conteudo
        assert artifact.id is not None

    def test_artifact_tipos_validos(self):
        for tipo in ("markdown", "pdf", "xlsx", "png", "json"):
            a = Artifact(thread_id="t1", tipo=tipo, conteudo="x")
            assert a.tipo == tipo

    def test_artifact_to_dict(self):
        a = Artifact(thread_id="t1", tipo="markdown", conteudo="teste")
        d = a.to_dict()
        assert "id" in d
        assert "thread_id" in d
        assert "tipo" in d
        assert "criado_em" in d
