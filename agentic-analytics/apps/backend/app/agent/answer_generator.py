"""Gerador de resposta final com LLM (Ollama) ou template."""
from __future__ import annotations
import json


def generate_answer(
    question: str,
    rag_context: str | None,
    sql_result: list[dict] | None,
    sql_query: str | None,
    sources: list[str],
    masked_fields: list[str],
    model: str = "llama3.2:1b",
) -> str:
    """Gera resposta em linguagem natural. Tenta Ollama; fallback para template."""
    try:
        return _call_ollama(question, rag_context, sql_result, sql_query, sources, masked_fields, model)
    except Exception:
        return _template_answer(question, rag_context, sql_result, sql_query, sources, masked_fields)


def _call_ollama(question, rag_context, sql_result, sql_query, sources, masked_fields, model):
    import httpx
    from app.config import settings
    context_parts = []
    if rag_context:
        context_parts.append(f"Contexto de regras:\n{rag_context[:2000]}")
    if sql_result:
        context_parts.append(f"Resultado SQL (primeiras 10 linhas):\n{json.dumps(sql_result[:10], ensure_ascii=False, default=str)}")
    if sql_query:
        context_parts.append(f"SQL executado:\n{sql_query}")
    if masked_fields:
        context_parts.append(f"Campos mascarados por política de privacidade: {', '.join(masked_fields)}")

    prompt = f"""Você é um analista sênior de pricing e risco. Responda em português do Brasil.

Pergunta: {question}

{chr(10).join(context_parts)}

Produza: 1) Resumo executivo 2) Análise dos dados 3) Próximos passos sugeridos.
Seja conciso e objetivo."""

    resp = httpx.post(
        f"{settings.OLLAMA_HOST}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def _template_answer(question, rag_context, sql_result, sql_query, sources, masked_fields):
    parts = [f"**Pergunta:** {question}\n"]
    if rag_context:
        parts.append(f"**Contexto de Regras:**\n{rag_context[:500]}...\n")
    if sql_result:
        parts.append(f"**Resultado Analítico ({len(sql_result)} linhas):**")
        for row in sql_result[:5]:
            parts.append(f"  - {row}")
    if sources:
        parts.append(f"\n**Fontes:** {', '.join(sources[:3])}")
    if masked_fields:
        parts.append(f"\n*Nota: Campos mascarados por política: {', '.join(masked_fields)}*")
    return "\n".join(parts)
