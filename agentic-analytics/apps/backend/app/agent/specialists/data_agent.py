"""
Data Agent — Especialista em extração de dados e RAG focado em números.
No futuro, envolverá chamadas diretas ao text2sql_agent.
"""
from __future__ import annotations


class DataAgent:
    """Especialista responsável por números, pricing, margem e consultas SQL/RAG."""

    async def process(self, question: str, trace_id: str | None = None) -> dict:
        """Processa a pergunta gerando a resposta e metadados."""
        from app.agent.text2sql_agent import run_text2sql
        from app.agent.rag_agent import search_rules

        # Faz RAG leve de cenário de dados
        chunks, sources = search_rules(question, top_k=2)
        context = "\n\n".join(chunks)

        sql, result, masked = run_text2sql(question, rag_context=context)

        return {
            "content": f"Executei a consulta SQL. Retornou {len(result)} linhas.",
            "sql": sql,
            "sql_result": result,
            "masked_fields": masked,
            "sources": sources,
        }
