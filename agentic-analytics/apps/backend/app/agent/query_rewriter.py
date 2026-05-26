"""Query rewriter — reescreve perguntas vagas para melhor recuperação."""
from __future__ import annotations
from app.agent.guardrail import GuardrailResult


def rewrite_query(
    question: str,
    guardrail_result: GuardrailResult | None = None,
    retrieval_feedback: str = "",
) -> str:
    """Reescreve pergunta para melhor precisão. Em produção: usa LLM."""
    q = question.strip()
    # Expansões simples de termos vagos
    replacements = {
        "última safra": "safra mais recente (SELECT MAX(safra) FROM fact_pricing_snapshot)",
        "alto risco": "clientes com score_risco >= 7",
        "pior": "menor valor de",
        "melhor": "maior valor de",
    }
    q_lower = q.lower()
    for term, expansion in replacements.items():
        if term in q_lower:
            q = q.replace(term, expansion)
            break
    return q if q != question else f"{question} — com dados agregados por segmento e safra"
