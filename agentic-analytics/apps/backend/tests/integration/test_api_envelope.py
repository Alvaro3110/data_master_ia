import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def assert_envelope(payload: dict) -> dict:
    assert "trace_id" in payload
    assert isinstance(payload["trace_id"], str)
    assert payload["trace_id"]
    assert "data" in payload
    return payload["data"]


@pytest.mark.asyncio
async def test_health_returns_envelope(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = assert_envelope(response.json())
    assert "status" in data


@pytest.mark.asyncio
async def test_workspaces_endpoints_return_envelope(client):
    create_resp = await client.post(
        "/api/v1/workspaces",
        json={"nome": "WS Envelope", "user_id": "env-u1"},
    )
    assert create_resp.status_code == 201
    created = assert_envelope(create_resp.json())
    assert "id" in created

    list_resp = await client.get("/api/v1/workspaces?user_id=env-u1")
    assert list_resp.status_code == 200
    listed = assert_envelope(list_resp.json())
    assert isinstance(listed, list)


@pytest.mark.asyncio
async def test_search_rules_returns_envelope(client, monkeypatch):
    def fake_search(query: str, top_k: int = 5):
        return ["regra-a", "regra-b"], ["source-a.md"]

    monkeypatch.setattr("app.api.v1.search_rules._search", fake_search)

    response = await client.post(
        "/api/v1/search-rules",
        json={"query": "qual regra de risco", "top_k": 2},
    )
    assert response.status_code == 200
    data = assert_envelope(response.json())
    assert data["total"] == 2
    assert data["chunks"] == ["regra-a", "regra-b"]


@pytest.mark.asyncio
async def test_stream_start_returns_envelope(client):
    response = await client.post(
        "/api/v1/ask-analytics/stream",
        json={"question": "Teste envelope stream"},
    )
    assert response.status_code == 200
    data = assert_envelope(response.json())
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_traces_not_found_still_returns_envelope(client):
    response = await client.get("/api/v1/traces/trace-inexistente-123")
    assert response.status_code == 404
    data = assert_envelope(response.json())
    assert "detail" in data
