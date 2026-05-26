import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app

client = TestClient(app)


@patch("httpx.AsyncClient.get")
@patch("sqlalchemy.create_engine")
def test_health_check_all_ok(mock_create_engine, mock_get):
    """Teste onde todos os serviços estão saudáveis."""
    # Mock do ping no DB
    mock_engine = mock_create_engine.return_value
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    mock_conn.execute.return_value = True

    # Mock das requisições HTTP (OpenSearch e Ollama)
    mock_resp_os = MagicMock()
    mock_resp_os.json.return_value = {"status": "green"}
    mock_resp_os.status_code = 200

    mock_resp_ollama = MagicMock()
    mock_resp_ollama.status_code = 200

    # Retorna o mock do OS na primeira chamada e do Ollama na segunda
    mock_get.side_effect = [mock_resp_os, mock_resp_ollama]

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "services" in data
    assert data["services"]["opensearch"]["status"] == "healthy"
    assert data["services"]["ollama"]["status"] == "healthy"
    assert data["services"]["postgres"]["status"] == "healthy"


@patch("httpx.AsyncClient.get")
@patch("sqlalchemy.create_engine")
def test_health_check_degraded(mock_create_engine, mock_get):
    """Teste onde um serviço falha, resultando em status degraded."""
    # Mock falha no DB
    mock_create_engine.side_effect = Exception("DB Connection Refused")

    mock_resp_os = MagicMock()
    mock_resp_os.json.return_value = {"status": "green"}
    mock_resp_os.status_code = 200

    mock_resp_ollama = MagicMock()
    mock_resp_ollama.status_code = 200

    mock_get.side_effect = [mock_resp_os, mock_resp_ollama]

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["postgres"]["status"] == "unhealthy"
    assert "DB Connection Refused" in data["services"]["postgres"]["detail"]
