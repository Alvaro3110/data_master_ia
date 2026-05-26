"""
Risk Agent — Especialista em políticas de risco e crédito.
Analisa a viabilidade e os riscos de métricas e cenários levantados pelo Data Agent ou usuário.
"""
from __future__ import annotations


class RiskAgent:
    """Especialista responsável por avaliação de risco, limites e políticas."""

    async def process(self, question: str, trace_id: str | None = None) -> dict:
        """Processa a pergunta gerando a resposta especializada em risco."""
        from app.agent.rag_agent import search_rules
        from app.agent.answer_generator import generate_answer
        from app.config import settings

        chunks, sources = search_rules(question, top_k=3)
        context = "\n\n".join(chunks)
        
        # Gera uma resposta LLM baseada apenas nas regras de risco
        answer = generate_answer(
            question=question,
            rag_context=context,
            sql_result=None,
            sql_query=None,
            sources=sources,
            masked_fields=[],
            model=settings.OLLAMA_MODEL,
        )

        return {
            "content": answer,
            "sources": sources,
        }
