"""
Testes unitários do Guardrail.
Usa o fallback heurístico (sem LLM) para testes rápidos.
"""
import pytest

from unittest.mock import patch
from app.agent.guardrail import classify_question, _heuristic_classify


# Patcha o Ollama para usar apenas heurística nos unit tests
def _mock_classify(question: str):
    """Usa heurística diretamente sem LLM."""
    from app.agent.guardrail import GuardrailResult
    data = _heuristic_classify(question)
    score = int(data["score"])
    return GuardrailResult(
        allowed=data["allowed"] and score >= 60,
        score=score,
        intent=data["intent"],
        sensitivity_flag=data["sensitivity_flag"],
        reason=data["reason"],
        rewrite_suggestion=data.get("rewrite_suggestion"),
    )


# ─── Out of scope ──────────────────────────────────────────────────────────────

def test_guardrail_rejeita_capital_franca():
    res = _mock_classify("Qual é a capital da França?")
    assert res.allowed is False
    assert res.score < 60
    assert res.intent == "out_of_scope"


def test_guardrail_rejeita_futebol():
    res = _mock_classify("Qual time ganhou o campeonato de futebol?")
    assert res.allowed is False


def test_guardrail_rejeita_clima():
    res = _mock_classify("Como está o tempo em São Paulo hoje?")
    assert res.allowed is False


def test_guardrail_rejeita_saudacao():
    # Não tem keywords do domínio
    res = _mock_classify("Olá, tudo bem?")
    assert res.allowed is False


# ─── In scope — pricing/risco ─────────────────────────────────────────────────

def test_guardrail_aceita_pergunta_de_margem():
    res = _mock_classify("Qual segmento teve pior margem na última safra?")
    assert res.allowed is True
    assert res.intent in {"analytics", "hybrid"}
    assert res.score >= 60


def test_guardrail_aceita_pergunta_de_roae():
    res = _mock_classify("Compare ROAE por safra nos clientes de alto risco")
    assert res.allowed is True
    assert res.intent in {"analytics", "hybrid"}


def test_guardrail_aceita_pergunta_conceitual():
    res = _mock_classify("O que significa safra nesta base?")
    assert res.allowed is True
    assert res.intent == "conceptual"


def test_guardrail_aceita_pergunta_hibrida():
    res = _mock_classify("Explique a regra de alto risco e compare inadimplência por safra")
    assert res.allowed is True
    assert res.intent == "hybrid"


def test_guardrail_aceita_pergunta_de_pricing():
    res = _mock_classify("Quais produtos tiveram pior ROAE na última safra?")
    assert res.allowed is True


def test_guardrail_aceita_pergunta_de_score_risco():
    res = _mock_classify("Quantos clientes têm score de risco acima de 7?")
    assert res.allowed is True


# ─── Campos do resultado ──────────────────────────────────────────────────────

def test_resultado_tem_todos_os_campos():
    res = _mock_classify("Qual a margem média por segmento?")
    assert hasattr(res, "allowed")
    assert hasattr(res, "score")
    assert hasattr(res, "intent")
    assert hasattr(res, "sensitivity_flag")
    assert hasattr(res, "reason")
    assert hasattr(res, "rewrite_suggestion")


def test_score_range():
    for q in [
        "Qual a margem?",
        "Qual é a capital da França?",
        "Compare ROAE por safra",
    ]:
        res = _mock_classify(q)
        assert 0 <= res.score <= 100
