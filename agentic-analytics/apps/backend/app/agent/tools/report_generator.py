"""
Report Generator — Fase 3: Geração de relatórios Markdown estruturados.
Gera relatórios executivos a partir de:
- Pergunta original do usuário
- SQL executado (para rastreabilidade/auditoria)
- Rows resultantes da consulta
- Contexto semântico do RAG
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional


class ReportGenerator:
    """
    Gera relatórios Markdown estruturados seguindo o padrão do evolution.md:
    1. Resumo Executivo
    2. Leitura Analítica
    3. Riscos e Limitações
    4. Próximos Passos
    """

    def generate(
        self,
        question: str,
        sql: str,
        rows: list[dict],
        rag_context: str = "",
        trace_id: Optional[str] = None,
        masked_fields: Optional[list[str]] = None,
    ) -> str:
        """
        Gera relatório Markdown completo.

        Args:
            question: Pergunta original do usuário.
            sql: SQL executado (para auditoria).
            rows: Resultado da consulta SQL.
            rag_context: Contexto semântico do RAG.
            trace_id: ID de rastreabilidade.
            masked_fields: Campos mascarados por política.

        Returns:
            String em Markdown formatado.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        n_rows = len(rows)
        has_data = n_rows > 0

        sections = []

        # ── Cabeçalho ────────────────────────────────────────────────────────
        sections.append(f"# Relatório Analítico\n")
        sections.append(f"**Gerado em:** {now}  ")
        if trace_id:
            sections.append(f"**Trace ID:** `{trace_id}`  ")
        sections.append(f"\n---\n")

        # ── 1. Resumo Executivo ───────────────────────────────────────────────
        sections.append("## Resumo Executivo\n")
        sections.append(f"**Pergunta:** {question}\n")
        if has_data:
            sections.append(
                f"A consulta retornou **{n_rows} registro(s)**. "
                f"Os principais resultados estão detalhados na seção analítica abaixo."
            )
            if rag_context:
                sections.append(f"\n\n**Contexto de Negócio:** {rag_context[:300]}...")
        else:
            sections.append(
                "Nenhum resultado foi encontrado para os critérios especificados. "
                "Verifique se os filtros estão corretos ou se há dados disponíveis para o período selecionado."
            )

        sections.append("\n")

        # ── 2. Leitura Analítica ──────────────────────────────────────────────
        sections.append("## Leitura Analítica\n")
        if has_data:
            # Renderiza a tabela de dados
            headers = list(rows[0].keys())
            sections.append("| " + " | ".join(headers) + " |")
            sections.append("| " + " | ".join(["---"] * len(headers)) + " |")
            for row in rows[:20]:  # máximo 20 linhas na tabela
                values = []
                for h in headers:
                    v = row.get(h, "")
                    if isinstance(v, float):
                        values.append(f"{v:.4f}")
                    else:
                        values.append(str(v))
                sections.append("| " + " | ".join(values) + " |")
            if n_rows > 20:
                sections.append(f"\n*... e mais {n_rows - 20} registros omitidos.*")
        else:
            sections.append("Sem dados para análise com os critérios fornecidos.")

        sections.append("\n")

        # ── SQL Auditável ─────────────────────────────────────────────────────
        sections.append("## SQL Executado\n")
        sections.append(f"```sql\n{sql}\n```\n")

        # ── 3. Riscos e Limitações ────────────────────────────────────────────
        sections.append("## Riscos e Limitações\n")
        limitacoes = []
        if not has_data:
            limitacoes.append("- Nenhum dado retornado — pode indicar filtro muito restritivo ou ausência de dados para o período.")
        if masked_fields:
            limitacoes.append(f"- Campos mascarados por política de governança: `{'`, `'.join(masked_fields)}`.")
        limitacoes.append("- Os resultados refletem o estado da base de dados no momento da consulta.")
        limitacoes.append("- Causalidade não pode ser inferida apenas a partir de correlações observadas.")
        limitacoes.append("- Consulte a equipe de dados antes de tomar decisões com base exclusivamente neste relatório.")

        sections.extend(limitacoes)
        sections.append("\n")

        # ── 4. Próximos Passos ────────────────────────────────────────────────
        sections.append("## Próximos Passos Sugeridos\n")
        sections.append("1. Validar os resultados com a equipe de Pricing e Risco.")
        sections.append("2. Comparar com safras anteriores para identificar tendências.")
        sections.append("3. Aprofundar a análise em segmentos ou produtos específicos.")
        sections.append("4. Registrar os achados no workspace para referência futura.")

        return "\n".join(sections)
