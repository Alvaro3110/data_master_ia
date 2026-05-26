"""
TDD — Fase 4: Integração Swarm Routing.
Verifica se o graph.py ou o endpoint chamam o Orchestrator e retornam a resposta consolidada.
"""
import pytest
from app.agent.orchestrator import Orchestrator, SwarmMessage
from app.agent.specialists.data_agent import DataAgent
from app.agent.specialists.risk_agent import RiskAgent


@pytest.mark.asyncio
async def test_full_swarm_routing():
    """Simula o fluxo completo de orquestração do swarm."""
    orchestrator = Orchestrator()
    data_agent = DataAgent()
    risk_agent = RiskAgent()

    question = "Calcule a margem e qual o risco disso?"
    
    # 1. Orquestrador decide a rota
    route = orchestrator.route(question)
    assert "data_agent" in route.required_agents
    assert "risk_agent" in route.required_agents
    
    # 2. Executa os agentes necessários
    messages = []
    if "data_agent" in route.required_agents:
        data_resp = await data_agent.process(question)
        messages.append(SwarmMessage(agent="data_agent", content=data_resp["content"]))
        
    if "risk_agent" in route.required_agents:
        risk_resp = await risk_agent.process(question)
        messages.append(SwarmMessage(agent="risk_agent", content=risk_resp["content"]))
        
    # 3. Orquestrador sintetiza
    final_answer = orchestrator.synthesize(question, messages)
    assert "DATA_AGENT" in final_answer
    assert "RISK_AGENT" in final_answer
