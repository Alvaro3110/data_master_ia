"""
TDD — Fase 4: Swarm Orchestration (Supervisor + Especialistas)
Testa se o Supervisor (Orchestrator) consegue:
- Receber a pergunta e decidir qual agente chamar
- Passar o contexto correto para o Data Agent (SQL/RAG)
- Passar o contexto correto para o Risk Agent (Avaliação de Risco)
- Agregar as respostas em um veredito final
"""
import pytest
from app.agent.orchestrator import Orchestrator, SwarmMessage


class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()

    def test_routing_to_data_agent(self, orchestrator):
        """Perguntas sobre números (margem, safra, pricing) vão para Data Agent."""
        route = orchestrator.route("Qual a margem da safra 2026-03?")
        assert route.target_agent == "data_agent"

    def test_routing_to_risk_agent(self, orchestrator):
        """Perguntas sobre risco, inadimplência e política vão para Risk Agent."""
        route = orchestrator.route("Qual o risco de aprovar crédito corporativo sem garantia?")
        assert route.target_agent == "risk_agent"

    def test_routing_hybrid_requires_both(self, orchestrator):
        """Perguntas complexas exigem ambos os agentes (workflow paralelo/sequencial)."""
        route = orchestrator.route("Calcule a margem e avalie o risco da safra 2026-03.")
        assert "data_agent" in route.required_agents
        assert "risk_agent" in route.required_agents

    def test_aggregate_responses(self, orchestrator):
        """O orquestrador deve compilar as respostas dos especialistas."""
        data_resp = SwarmMessage(agent="data_agent", content="Margem é 2.5%")
        risk_resp = SwarmMessage(agent="risk_agent", content="Risco é moderado devido ao ROAE")
        
        final_answer = orchestrator.synthesize(
            question="Margem e risco?",
            messages=[data_resp, risk_resp]
        )
        assert "2.5%" in final_answer
        assert "moderado" in final_answer
