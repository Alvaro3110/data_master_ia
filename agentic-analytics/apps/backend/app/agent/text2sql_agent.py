"""
Text2SQL Agent — Fase 1: LLM-driven com saída JSON estruturada.
Padrão: prompt estruturado → Ollama → JSON {decision, sql, tables_used, ...}
Fallback: keyword matching para quando o LLM não está disponível.
O SQL gerado é sempre validado pelo sql_validator (SQLGlot AST).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.security.masking import DEFAULT_SENSITIVE_FIELDS, apply_masking
from app.security.sql_validator import validate_sql

logger = logging.getLogger(__name__)

# Caminho do scenarios.md — semântica de negócio para injeção no prompt
_SCENARIOS_PATH = (
    Path(__file__).parent.parent.parent.parent.parent / "data" / "docs" / "scenarios.md"
)

# ── Modelo de resultado ──────────────────────────────────────────────────────

@dataclass
class Text2SQLResult:
    """Resultado estruturado do agente Text2SQL."""
    decision: str  # "sql" | "blocked" | "needs_rule_context" | "clarify" | "fallback"
    sql: Optional[str] = None
    tables_used: list[str] = field(default_factory=list)
    columns_used: list[str] = field(default_factory=list)
    estimated_granularity: str = "unknown"
    explanation: Optional[str] = None
    safety_notes: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    masked_fields: list[str] = field(default_factory=list)
    error: Optional[str] = None


# ── Prompt de geração SQL ────────────────────────────────────────────────────

_SQL_GENERATION_PROMPT = """Você é um agente Text-to-SQL corporativo para analytics de pricing e risco financeiro.

Objetivo: gerar SQL somente leitura, seguro, auditável e alinhado ao schema e aos scenarios abaixo.

Regras obrigatórias:
- Use APENAS as tabelas e colunas listadas no schema_catalog.
- Priorize resultados AGREGADOS (AVG, COUNT, SUM) em vez de dados por cliente.
- Sempre inclua LIMIT quando a tabela fact_pricing_snapshot for usada.
- Se a pergunta citar "última safra", use: (SELECT MAX(safra) FROM fact_pricing_snapshot)
- Se a pergunta citar "alto risco", use: score_risco >= 7
- NUNCA use DDL, DML, procedures, COPY, UNLOAD, múltiplas statements.
- Nunca acesse colunas: cpf, nome_cliente diretamente sem masking.
- Se a pergunta não puder ser respondida com segurança, use decision=blocked.
- Se precisar de contexto de regras/glossário, use decision=needs_rule_context.

Tabelas autorizadas: fact_pricing_snapshot, dim_cliente, dim_produto, metric_catalog, schema_catalog

Scenarios (semântica de negócio):
{scenarios}

Pergunta do usuário: {question}

Contexto RAG adicional: {rag_context}

Responda APENAS com JSON válido neste formato exato:
{{
  "decision": "sql",
  "sql": "SELECT ...",
  "tables_used": ["fact_pricing_snapshot"],
  "columns_used": ["safra", "margem_liquida"],
  "estimated_granularity": "aggregated",
  "explanation": "Explicação breve do que a query retorna.",
  "safety_notes": []
}}"""


# ── Agente ───────────────────────────────────────────────────────────────────

class Text2SQLAgent:
    """
    Agente Text2SQL orientado a LLM.
    Usa Ollama para geração de SQL via prompt estruturado com saída JSON.
    Valida o SQL gerado com SQLGlot AST antes de executar.
    Faz fallback para keyword matching se o LLM não estiver disponível.
    """

    def __init__(self):
        self._scenarios: Optional[str] = None

    def _load_scenarios(self) -> str:
        """Carrega scenarios.md para injeção no prompt."""
        if self._scenarios is None:
            try:
                self._scenarios = _SCENARIOS_PATH.read_text(encoding="utf-8")
            except FileNotFoundError:
                logger.warning(f"scenarios.md não encontrado em {_SCENARIOS_PATH}")
                self._scenarios = "Sem scenarios disponíveis."
        return self._scenarios

    async def _call_llm(self, prompt: str) -> str:
        """Chama o LLM Provider configurado com o prompt e retorna a resposta como string."""
        from app.services.llm_provider import generate_response
        return await generate_response(prompt=prompt, model=settings.OLLAMA_MODEL)

    async def generate_sql(
        self,
        question: str,
        rag_context: str = "",
    ) -> Text2SQLResult:
        """
        Gera SQL via LLM com validação AST.
        Retorna Text2SQLResult com decision, sql, explicação e notas de segurança.
        """
        scenarios = self._load_scenarios()
        prompt = _SQL_GENERATION_PROMPT.format(
            scenarios=scenarios[:3000],  # limita para não exceder context window
            question=question,
            rag_context=rag_context[:500] if rag_context else "Nenhum.",
        )

        # ── Tenta LLM ────────────────────────────────────────────────────────
        try:
            raw = await self._call_llm(prompt)
            parsed = self._parse_llm_response(raw)
            if parsed:
                return self._validate_and_finalize(parsed)
        except Exception as e:
            logger.warning(f"LLM indisponível ou erro: {e} — usando fallback keyword matching")

        # ── Fallback: keyword matching ────────────────────────────────────────
        sql = _infer_sql(question)
        if sql:
            verdict = validate_sql(sql)
            if verdict.allowed:
                return Text2SQLResult(
                    decision="fallback",
                    sql=sql,
                    tables_used=["fact_pricing_snapshot"],
                    explanation="SQL gerado por keyword matching (LLM indisponível).",
                )
            else:
                return Text2SQLResult(
                    decision="blocked",
                    sql=None,
                    explanation=f"SQL de fallback bloqueado: {verdict.reasons}",
                )

        return Text2SQLResult(
            decision="clarify",
            sql=None,
            explanation="Não foi possível gerar SQL — reformule a pergunta.",
        )

    def _parse_llm_response(self, raw: str) -> Optional[dict]:
        """Tenta parsear a resposta do LLM como JSON."""
        if not raw:
            return None
        # Tenta parse direto
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Tenta extrair JSON de dentro de markdown ```json ... ```
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    def _validate_and_finalize(self, parsed: dict) -> Text2SQLResult:
        """Valida o SQL gerado pelo LLM com o SQLGlot AST validator."""
        decision = parsed.get("decision", "sql")
        sql = parsed.get("sql")

        # Decisões sem SQL — propagam direto
        if decision in ("blocked", "needs_rule_context", "clarify") or not sql:
            return Text2SQLResult(
                decision=decision,
                sql=None,
                tables_used=parsed.get("tables_used", []),
                columns_used=parsed.get("columns_used", []),
                estimated_granularity=parsed.get("estimated_granularity", "unknown"),
                explanation=parsed.get("explanation"),
                safety_notes=parsed.get("safety_notes", []),
            )

        # Valida o SQL gerado com SQLGlot AST
        verdict = validate_sql(sql)
        if not verdict.allowed:
            logger.warning(f"SQL gerado pelo LLM foi bloqueado pelo validator: {verdict.reasons}")
            return Text2SQLResult(
                decision="blocked",
                sql=None,
                explanation=f"SQL rejeitado pelo validator: {'; '.join(verdict.reasons)}",
                safety_notes=verdict.reasons,
            )

        return Text2SQLResult(
            decision="sql",
            sql=sql,
            tables_used=parsed.get("tables_used", []),
            columns_used=parsed.get("columns_used", []),
            estimated_granularity=parsed.get("estimated_granularity", "aggregated"),
            explanation=parsed.get("explanation"),
            safety_notes=parsed.get("safety_notes", []),
        )

    async def execute(
        self,
        question: str,
        rag_context: str = "",
    ) -> Text2SQLResult:
        """
        Gera SQL, valida e executa no DuckDB.
        Retorna Text2SQLResult com rows e masked_fields preenchidos.
        """
        result = await self.generate_sql(question, rag_context)

        if result.sql is None or result.decision not in ("sql", "fallback"):
            return result

        try:
            rows, masked_fields = await self._execute_duckdb(result.sql)
            result.rows = rows
            result.masked_fields = masked_fields
        except Exception as e:
            logger.error(f"Erro ao executar SQL no DuckDB: {e}")
            result.error = str(e)
            result.rows = []

        return result

    async def _execute_duckdb(self, sql: str) -> tuple[list[dict], list[str]]:
        """Executa SQL no DuckDB e retorna rows mascarados."""
        import duckdb
        from pathlib import Path as P

        db_path = P(settings.DUCKDB_PATH)
        seed_json = (
            P(__file__).parent.parent.parent.parent.parent
            / "data" / "seeds" / "pricing_snapshot.json"
        )

        conn = duckdb.connect(str(db_path) if db_path.exists() else ":memory:")
        if seed_json.exists():
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS fact_pricing_snapshot "
                f"AS SELECT * FROM read_json_auto('{str(seed_json)}')"
            )

        result = conn.execute(sql).fetchdf()
        conn.close()

        rows = result.to_dict("records")
        masked = apply_masking(rows, DEFAULT_SENSITIVE_FIELDS)
        masked_fields = list({
            f for row in masked
            if row.get("_masked_fields")
            for f in row["_masked_fields"]
        })
        clean = [{k: v for k, v in row.items() if k != "_masked_fields"} for row in masked]
        return clean[:settings.SQL_MAX_ROWS], masked_fields


async def run_text2sql(
    question: str,
    rag_context: str = "",
) -> tuple[str | None, list[dict], list[str]]:
    """
    Wrapper assíncrono para compatibilidade com o graph.py atual.
    """
    agent = Text2SQLAgent()
    result = await agent.execute(question, rag_context)
    return result.sql, result.rows, result.masked_fields


# ── Keyword matching (fallback legado) ───────────────────────────────────────

def _infer_sql(question: str) -> str | None:
    """Infere SQL baseado em palavras-chave. Fallback quando LLM está indisponível."""
    q = question.lower()

    if "última safra" in q or "ultimo safra" in q or "last safra" in q:
        if "roae" in q:
            return """SELECT segmento, AVG(roae) as roae_medio, COUNT(*) as contratos
FROM fact_pricing_snapshot
WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
GROUP BY segmento ORDER BY roae_medio LIMIT 50"""
        if "margem" in q:
            return """SELECT segmento, AVG(margem_liquida) as margem_media, COUNT(*) as contratos
FROM fact_pricing_snapshot
WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
GROUP BY segmento ORDER BY margem_media LIMIT 50"""

    if "alto risco" in q or "score_risco" in q:
        return """SELECT safra, segmento, COUNT(*) as clientes_alto_risco, AVG(roae) as roae_medio
FROM fact_pricing_snapshot
WHERE score_risco >= 7
GROUP BY safra, segmento ORDER BY safra DESC, clientes_alto_risco DESC LIMIT 50"""

    if "margem" in q:
        return """SELECT safra, segmento, AVG(margem_liquida) as margem_media
FROM fact_pricing_snapshot GROUP BY safra, segmento
ORDER BY safra DESC, margem_media LIMIT 100"""

    if "roae" in q:
        return """SELECT safra, segmento, AVG(roae) as roae_medio
FROM fact_pricing_snapshot GROUP BY safra, segmento
ORDER BY safra DESC, roae_medio LIMIT 100"""

    if "inadimplência" in q or "inadimplente" in q:
        return """SELECT safra,
    COUNT(*) as total,
    SUM(CASE WHEN inadimplente THEN 1 ELSE 0 END) as inadimplentes,
    ROUND(AVG(CASE WHEN inadimplente THEN 1.0 ELSE 0.0 END) * 100, 2) as taxa_inad
FROM fact_pricing_snapshot GROUP BY safra ORDER BY safra DESC LIMIT 24"""

    return """SELECT safra, segmento, COUNT(*) as contratos,
    AVG(margem_liquida) as margem_media, AVG(roae) as roae_medio
FROM fact_pricing_snapshot GROUP BY safra, segmento
ORDER BY safra DESC, segmento LIMIT 100"""
