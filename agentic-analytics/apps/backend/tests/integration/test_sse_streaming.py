import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.redis_client import redis_mgr

client = TestClient(app)


@pytest.mark.asyncio
async def test_sse_stream_replay_buffer():
    """Valida que o replay buffer do Redis filtra os eventos anteriores ao last_event_id."""
    trace_id = "test-replay-trace-id"
    
    # 1. Limpa qualquer stream anterior
    await redis_mgr.redis.delete(f"stream:{trace_id}")
    
    # 2. Adiciona 3 eventos fictícios ao stream
    id1 = await redis_mgr.add_event(trace_id, "start", {"q": "teste 1"})
    id2 = await redis_mgr.add_event(trace_id, "step", {"step": "processando"})
    id3 = await redis_mgr.add_event(trace_id, "done", {"trace_id": trace_id, "answer": "finalizado"})
    
    # 3. Consome sem last_event_id (deve retornar todos os 3)
    response = client.get(f"/api/v1/ask-analytics/stream/{trace_id}")
    assert response.status_code == 200
    lines = [line for line in response.text.split("\n") if line]
    
    # Cada evento tem: id, event, data (3 linhas por evento)
    assert len(lines) >= 9
    assert f"id: {id1}" in lines
    assert f"id: {id2}" in lines
    assert f"id: {id3}" in lines

    # 4. Consome passando last_event_id correspondente ao id1 (deve pular id1 e trazer id2, id3)
    response_replay = client.get(f"/api/v1/ask-analytics/stream/{trace_id}?last_event_id={id1}")
    assert response_replay.status_code == 200
    lines_replay = [line for line in response_replay.text.split("\n") if line]
    
    assert f"id: {id1}" not in lines_replay
    assert f"id: {id2}" in lines_replay
    assert f"id: {id3}" in lines_replay


@pytest.mark.asyncio
async def test_full_sse_workflow(monkeypatch):
    """Valida o fluxo SSE completo de POST para iniciar e GET para ouvir os eventos."""
    # Mock do run_analytics_stream para rodar rápido e determinístico
    async def mock_run_analytics_stream(question, trace_id, config=None):
        await redis_mgr.add_event(trace_id, "start", {"question": question})
        await redis_mgr.add_event(trace_id, "step", {"node": "guardrail", "reasoning_step": "ok"})
        await redis_mgr.add_event(trace_id, "chunk", {"text": "Resposta"})
        await redis_mgr.add_event(trace_id, "chunk", {"text": " mockada"})
        await redis_mgr.add_event(trace_id, "done", {"trace_id": trace_id, "answer": "Resposta mockada", "status": "success"})

    monkeypatch.setattr("app.agent.graph.run_analytics_stream", mock_run_analytics_stream)

    # 1. Dispara fluxo de streaming
    res_post = client.post(
        "/api/v1/ask-analytics/stream",
        json={"question": "Qual a margem da safra 2026?"}
    )
    assert res_post.status_code == 200
    trace_id = res_post.json()["data"]["trace_id"]
    assert trace_id is not None

    # Aguarda o processamento em background (mockado) persistir no Redis
    await asyncio.sleep(0.5)

    # 2. Consome o SSE endpoint
    response = client.get(f"/api/v1/ask-analytics/stream/{trace_id}")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    text = response.text
    assert "event: start" in text
    assert "event: step" in text
    assert "event: chunk" in text
    assert "event: done" in text
    assert "Resposta mockada" in text
