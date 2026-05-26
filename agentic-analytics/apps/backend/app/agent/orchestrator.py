"""
Orchestrator (Supervisor) — Fase 4: Swarm Orchestration.
Analisa a intenção da pergunta e decide quais agentes especialistas chamar.
Consolida as respostas geradas.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from app.agent.tools.sandbox_executor import SandboxExecutor


@dataclass
class SwarmRoute:
    """Rota decidida pelo orquestrador."""
    target_agent: str
    required_agents: list[str] = field(default_factory=list)


@dataclass
class SwarmMessage:
    """Mensagem de um agente especialista."""
    agent: str
    content: str


class Orchestrator:
    """
    Supervisor do Swarm.
    Roteia a intenção e sintetiza respostas.
    """

    def route(self, question: str) -> SwarmRoute:
        """
        Analisa a pergunta e decide a rota.
        Regras (hardcoded MVP, no futuro via LLM):
        - Palavras como "risco", "inadimplência", "política", "avaliar" -> Risk Agent
        - Palavras como "margem", "safra", "pricing", "número", "calcular" -> Data Agent
        - Combinações requerem ambos.
        """
        q = question.lower()
        needs_risk = any(word in q for word in ["risco", "inadimpl", "política", "avali", "aprov"])
        needs_data = any(word in q for word in ["margem", "safra", "pricing", "calcular", "roae", "número"])

        if needs_risk and needs_data:
            return SwarmRoute(target_agent="supervisor", required_agents=["data_agent", "risk_agent"])
        elif needs_risk:
            return SwarmRoute(target_agent="risk_agent", required_agents=["risk_agent"])
        else:
            return SwarmRoute(target_agent="data_agent", required_agents=["data_agent"])

    def synthesize(self, question: str, messages: list[SwarmMessage]) -> str:
        """
        Compila as respostas dos especialistas em um veredito final.
        (Neste MVP, apenas concatena com formatação; idealmente usa LLM)
        """
        if not messages:
            return "Nenhuma resposta dos especialistas."

        if len(messages) == 1:
            return messages[0].content

        final_answer = "### Veredito Final Consolidado\n\n"
        for msg in messages:
            final_answer += f"**[{msg.agent.upper()}]**\n{msg.content}\n\n"

        return final_answer.strip()
