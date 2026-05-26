"""
Guardrail — classificação de intenção e validação de escopo.
Padrão: Week7 Agentic RAG com score 0-100 e threshold=60.
Usa LLM com prompt do deep-research-report.md.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

import httpx

from app.config import settings

Intent = Literal["conceptual", "analytics", "hybrid", "out_of_scope"]
Sensitivity = Literal["low", "medium", "high"]


@dataclass
class GuardrailResult:
    allowed: bool
    score: int
    intent: Intent
    sensitivity_flag: Sensitivity
    reason: str
    rewrite_suggestion: str | None = None


# Prompt exato do deep-research-report.md
GUARDRAIL_PROMPT = """Você é o guardrail de um sistema analítico governado para pricing, margem, safra, risco e ROAE.

Sua tarefa é classificar a pergunta do usuário e devolver JSON válido.

Regras:
- O domínio permitido inclui: pricing, margem, spread, safra, risco, ROAE, rentabilidade, produto, segmento, cluster, carteira, inadimplência, garantia, política comercial, regras de negócio, documentação técnica e métricas relacionadas.
- Se a pergunta estiver fora do domínio, marque allowed=false.
- Se a pergunta pedir ação destrutiva, extração massiva de dados sensíveis, ou instruções que violem política de acesso, marque allowed=false.
- Se a pergunta estiver no domínio, defina intent como:
  - "conceptual" para definição/regra/política
  - "analytics" para consulta quantitativa/tabular
  - "hybrid" quando exigir regra + dado
- Dê um score de 0 a 100.
- Sugira rewrite apenas se a pergunta estiver vaga, mas ainda válida.
- Nunca gere SQL.
- Nunca invente tabela ou coluna.

Saída JSON (apenas o JSON, sem markdown):
{
  "allowed": true,
  "score": 0,
  "intent": "conceptual|analytics|hybrid|out_of_scope",
  "rewrite_suggestion": null,
  "sensitivity_flag": "low|medium|high",
  "reason": "..."
}

Pergunta:
{question}"""


def _parse_guardrail_response(raw: str) -> dict:
    """Extrai JSON do response do LLM (pode ter texto extra)."""
    # Tenta extrair JSON de bloco markdown ou raw
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError(f"Não foi possível extrair JSON do response: {raw[:200]}")


def classify_question(question: str) -> GuardrailResult:
    """
    Classifica uma pergunta usando o guardrail LLM.

    Score >= 60 (GUARDRAIL_THRESHOLD) → allowed=True.
    Implementação:
    1. Tenta Ollama local (sem custo, privacidade)
    2. Fallback para regras heurísticas se LLM indisponível
    """
    prompt = GUARDRAIL_PROMPT.replace("{question}", question)

    try:
        result = _call_ollama(prompt)
        data = _parse_guardrail_response(result)
    except Exception:
        # Fallback heurístico se LLM offline
        data = _heuristic_classify(question)

    score = int(data.get("score", 0))
    allowed_by_llm = data.get("allowed", False)
    # Threshold Week7: score >= 60
    allowed = allowed_by_llm and score >= settings.GUARDRAIL_THRESHOLD

    return GuardrailResult(
        allowed=allowed,
        score=score,
        intent=data.get("intent", "out_of_scope"),
        sensitivity_flag=data.get("sensitivity_flag", "low"),
        reason=data.get("reason", ""),
        rewrite_suggestion=data.get("rewrite_suggestion"),
    )


def _call_ollama(prompt: str) -> str:
    """Chama Ollama sync para o guardrail."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }
    resp = httpx.post(
        f"{settings.OLLAMA_HOST}/api/generate",
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["response"]


# Palavras-chave do domínio de pricing
_DOMAIN_KEYWORDS = {
    "margem", "spread", "safra", "risco", "roae", "pricing", "precificação",
    "inadimplência", "segmento", "produto", "carteira", "rentabilidade",
    "cluster", "pme", "varejo", "atacado", "garantia", "score", "rating",
    "receita", "custo", "lucro", "patrimônio", "capital", "capital_giro",
}

_OUT_OF_SCOPE_KEYWORDS = {
    "capital da", "clima", "tempo", "receita de", "futebol", "política",
    "crime", "médico", "saúde", "cachorro", "gato", "animal",
}


def _heuristic_classify(question: str) -> dict:
    """Classificação heurística — fallback quando LLM está offline."""
    q_lower = question.lower()

    # Verifica out-of-scope
    for kw in _OUT_OF_SCOPE_KEYWORDS:
        if kw in q_lower:
            return {
                "allowed": False,
                "score": 10,
                "intent": "out_of_scope",
                "sensitivity_flag": "low",
                "reason": f"Pergunta fora do domínio de pricing/risco (heurística: '{kw}' detectado).",
                "rewrite_suggestion": None,
            }

    # Verifica se há keywords do domínio
    found_keywords = [kw for kw in _DOMAIN_KEYWORDS if kw in q_lower]
    if found_keywords:
        # Analytic vs conceptual
        analytic_words = {"qual", "quais", "compare", "comparar", "média", "total", "soma", "top", "pior", "melhor"}
        conceptual_words = {"o que", "como", "defina", "explique", "regra", "política", "significa"}
        has_analytic = any(w in q_lower for w in analytic_words)
        has_conceptual = any(w in q_lower for w in conceptual_words)
        intent = "hybrid" if has_analytic and has_conceptual else ("analytics" if has_analytic else "conceptual")
        return {
            "allowed": True,
            "score": 80,
            "intent": intent,
            "sensitivity_flag": "medium",
            "reason": f"Pergunta no domínio (heurística: {', '.join(found_keywords[:3])}).",
            "rewrite_suggestion": None,
        }

    return {
        "allowed": False,
        "score": 30,
        "intent": "out_of_scope",
        "sensitivity_flag": "low",
        "reason": "Pergunta fora do domínio de pricing/risco (heurística).",
        "rewrite_suggestion": None,
    }
