import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    """Verifica se origens permitidas (localhost:3000) têm acesso."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Requested-With",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_rejected_origin():
    """Verifica se origens desconhecidas não recebem os cabeçalhos de CORS."""
    headers = {
        "Origin": "http://malicious-site.com",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Requested-With",
    }
    response = client.options("/api/v1/health", headers=headers)
    # A resposta é 400 Bad Request devido à falha na origem no middleware CORS do FastAPI
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
