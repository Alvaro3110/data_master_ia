import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def unwrap(payload: dict):
    return payload["data"]


@pytest.mark.asyncio
async def test_ask_analytics_routing_sql(client):
    """Testa se a API responde a perguntas que disparam a rota analytics (SQL)."""
    response = await client.post(
        "/api/v1/ask-analytics",
        json={"question": "Qual foi a margem da última safra no segmento Varejo?"}
    )
    assert response.status_code == 200
    payload = response.json()
    data = unwrap(payload)
    
    assert "answer" in data
    assert payload["trace_id"]
    assert data["routed_path"] in ["analytics", "hybrid", "swarm_data_agent", "swarm_supervisor"]
    assert "reasoning_steps" in data
    assert data["sql"] is not None

@pytest.mark.asyncio
async def test_ask_analytics_routing_rag(client):
    """Testa se a API responde a perguntas conceituais disparando RAG."""
    response = await client.post(
        "/api/v1/ask-analytics",
        json={"question": "O que significa a sigla ROAE no glossário de pricing?"}
    )
    assert response.status_code == 200
    payload = response.json()
    data = unwrap(payload)
    
    assert "answer" in data
    assert payload["trace_id"]
    assert data["routed_path"] in ["conceptual", "rules_only", "hybrid", "swarm_risk_agent", "swarm_data_agent", "swarm_supervisor"]
    assert "reasoning_steps" in data

@pytest.mark.asyncio
async def test_ask_analytics_missing_question(client):
    """Testa a validação de request sem question."""
    response = await client.post("/api/v1/ask-analytics", json={})
    assert response.status_code == 422
