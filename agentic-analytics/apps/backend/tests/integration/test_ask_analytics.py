import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ask_analytics_routing_sql():
    """Testa se a API responde a perguntas que disparam a rota analytics (SQL)."""
    response = client.post(
        "/api/v1/ask-analytics",
        json={"question": "Qual foi a margem da última safra no segmento Varejo?"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert "trace_id" in data
    assert data["routed_path"] in ["analytics", "hybrid", "swarm_data_agent", "swarm_supervisor"]
    assert "reasoning_steps" in data
    assert data["sql"] is not None

def test_ask_analytics_routing_rag():
    """Testa se a API responde a perguntas conceituais disparando RAG."""
    response = client.post(
        "/api/v1/ask-analytics",
        json={"question": "O que significa a sigla ROAE no glossário de pricing?"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert "trace_id" in data
    assert data["routed_path"] in ["conceptual", "rules_only", "hybrid", "swarm_risk_agent", "swarm_data_agent", "swarm_supervisor"]
    assert "reasoning_steps" in data

def test_ask_analytics_missing_question():
    """Testa a validação de request sem question."""
    response = client.post("/api/v1/ask-analytics", json={})
    assert response.status_code == 422
