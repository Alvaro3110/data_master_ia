"""
TDD — Fase 4: Data Agent.
O Data Agent é o especialista em SQL e RAG de Pricing.
Na arquitetura Swarm, ele recebe perguntas roteadas para ele e gera as respostas analíticas.
"""
import pytest
from app.agent.specialists.data_agent import DataAgent


class TestDataAgent:
    @pytest.fixture
    def data_agent(self):
        return DataAgent()

    @pytest.mark.asyncio
    async def test_data_agent_process(self, data_agent):
        """O Data Agent processa e gera resposta (usando text2sql/RAG por baixo)."""
        response = await data_agent.process(
            question="Qual a margem média?",
            trace_id="test-123"
        )
        assert isinstance(response, dict)
        assert "content" in response
        assert "sql" in response
        assert "margem" in response["content"].lower() or "retornou" in response["content"].lower()
