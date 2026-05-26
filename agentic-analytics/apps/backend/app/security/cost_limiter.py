"""
Cost Limiter — bloqueia queries que excedem orçamento de cardinalidade.
Estima custo antes da execução e aborta se necessário.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings


@dataclass
class CostEstimate:
    allowed: bool
    estimated_rows: int | None
    reason: str | None = None


# Palavras-chave que indicam queries potencialmente caras
_EXPENSIVE_PATTERNS = [
    # Sem filtro temporal em tabela de fatos
    (re.compile(r"\bfact_pricing_snapshot\b(?!.*\bWHERE\b)", re.IGNORECASE | re.DOTALL), "Full scan on fact table without WHERE clause"),
    # Cross join implícito
    (re.compile(r"\bFROM\b.+\bFROM\b", re.IGNORECASE | re.DOTALL), "Possible cross join detected"),
    # Sem safra ou data
    (re.compile(r"SELECT\s+\*\s+FROM", re.IGNORECASE), "SELECT * without column projection"),
]


def estimate_cost(sql: str, row_count_hint: int | None = None) -> CostEstimate:
    """
    Estima custo da query antes de executar.

    Args:
        sql: Query SQL já validada (passou pelo sql_validator)
        row_count_hint: Cardinalidade estimada pelo DB (se disponível)

    Returns:
        CostEstimate com allowed=False se custo excede orçamento.
    """
    # Se a estimativa de rows excede o budget
    if row_count_hint is not None and row_count_hint > settings.COST_BUDGET_ROWS:
        return CostEstimate(
            allowed=False,
            estimated_rows=row_count_hint,
            reason=(
                f"Query would return ~{row_count_hint:,} rows, "
                f"exceeding budget of {settings.COST_BUDGET_ROWS:,}. "
                "Add a LIMIT or filter."
            ),
        )

    # Verificação estática de padrões caros
    for pattern, description in _EXPENSIVE_PATTERNS:
        if pattern.search(sql):
            return CostEstimate(
                allowed=False,
                estimated_rows=None,
                reason=f"Potentially expensive pattern: {description}. Add filters or LIMIT.",
            )

    return CostEstimate(allowed=True, estimated_rows=row_count_hint)
