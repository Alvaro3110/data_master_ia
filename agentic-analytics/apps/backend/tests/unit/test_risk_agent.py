"""
TDD — Fase 4: Risk Agent.
O Risk Agent é o especialista em políticas de crédito e risco.
Na arquitetura Swarm, ele avalia cenários usando as políticas de governança e RAG.
"""
import pytest
from app.agent.specialists.risk_agent import RiskAgent


class TestRiskAgent:
    @pytest.fixture
    def risk_agent(self):
        return RiskAgent()

    @pytest.mark.asyncio
    async def test_risk_agent_process(self, risk_agent):
        """O Risk Agent processa perguntas focadas em risco e política."""
        response = await risk_agent.process(
            question="Qual o risco aceitável para ROAE?",
            trace_id="test-456"
        )
        assert isinstance(response, dict)
        assert "content" in response
        # A resposta gerada pelo LLM depende do contexto mockado (ou LLM real se estiver rodando).
        assert len(response["content"]) > 0
