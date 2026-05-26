"""
TDD — Fase 2: Workspace API endpoints.
Testa que:
- POST /api/v1/workspaces cria workspace e retorna 201 com id
- GET /api/v1/workspaces lista workspaces do usuário
- GET /api/v1/workspaces/{id}/threads retorna threads do workspace
- POST /api/v1/workspaces/{id}/threads cria nova thread
- PUT /api/v1/workspaces/{id}/agent-md atualiza o agent.md
- POST /api/v1/ask-analytics aceita workspace_id opcional e persiste thread
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestWorkspaceEndpoints:
    @pytest.mark.asyncio
    async def test_cria_workspace(self, client):
        resp = await client.post("/api/v1/workspaces", json={
            "nome": "Análise Safra 2026-03",
            "user_id": "user-test-1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["nome"] == "Análise Safra 2026-03"
        assert data["user_id"] == "user-test-1"

    @pytest.mark.asyncio
    async def test_cria_workspace_sem_nome_retorna_422(self, client):
        resp = await client.post("/api/v1/workspaces", json={"user_id": "u1"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_lista_workspaces(self, client):
        # Cria dois workspaces
        await client.post("/api/v1/workspaces", json={"nome": "WS-A", "user_id": "u2"})
        await client.post("/api/v1/workspaces", json={"nome": "WS-B", "user_id": "u2"})

        resp = await client.get("/api/v1/workspaces?user_id=u2")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        nomes = [w["nome"] for w in data]
        assert "WS-A" in nomes
        assert "WS-B" in nomes

    @pytest.mark.asyncio
    async def test_cria_thread_em_workspace(self, client):
        # Cria workspace primeiro
        ws_resp = await client.post("/api/v1/workspaces", json={"nome": "WS-Thread", "user_id": "u3"})
        ws_id = ws_resp.json()["id"]

        # Cria thread
        resp = await client.post(f"/api/v1/workspaces/{ws_id}/threads", json={
            "titulo": "Análise de ROAE",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["workspace_id"] == ws_id
        assert data["titulo"] == "Análise de ROAE"

    @pytest.mark.asyncio
    async def test_lista_threads_de_workspace(self, client):
        ws_resp = await client.post("/api/v1/workspaces", json={"nome": "WS-List", "user_id": "u4"})
        ws_id = ws_resp.json()["id"]

        await client.post(f"/api/v1/workspaces/{ws_id}/threads", json={"titulo": "T1"})
        await client.post(f"/api/v1/workspaces/{ws_id}/threads", json={"titulo": "T2"})

        resp = await client.get(f"/api/v1/workspaces/{ws_id}/threads")
        assert resp.status_code == 200
        threads = resp.json()
        assert len(threads) >= 2

    @pytest.mark.asyncio
    async def test_atualiza_agent_md(self, client):
        ws_resp = await client.post("/api/v1/workspaces", json={"nome": "WS-MD", "user_id": "u5"})
        ws_id = ws_resp.json()["id"]

        resp = await client.put(f"/api/v1/workspaces/{ws_id}/agent-md", json={
            "agent_md": "Você é especialista em crédito PME. Sempre filtre por segmento='PME'.",
        })
        assert resp.status_code == 200
        assert "agent_md" in resp.json()
        assert "PME" in resp.json()["agent_md"]

    @pytest.mark.asyncio
    async def test_workspace_nao_encontrado_retorna_404(self, client):
        resp = await client.get("/api/v1/workspaces/id-inexistente/threads")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_ask_analytics_aceita_workspace_id(self, client):
        """POST /ask-analytics deve aceitar workspace_id sem quebrar."""
        ws_resp = await client.post("/api/v1/workspaces", json={"nome": "WS-Ask", "user_id": "u6"})
        ws_id = ws_resp.json()["id"]

        resp = await client.post("/api/v1/ask-analytics", json={
            "question": "Qual a margem por safra?",
            "workspace_id": ws_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "trace_id" in data
        assert "answer" in data
