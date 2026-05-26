"""
Data Masking — aplica hash/bucket/truncamento em campos sensíveis.
Baseado na especificação do deep-research-report.md.
"""
from __future__ import annotations

import hashlib
from typing import Any


# Campos sensíveis por padrão (classificação RESTRITA/SENSIVEL)
DEFAULT_SENSITIVE_FIELDS = {
    "cliente_id",
    "cpf",
    "cnpj",
    "nome_cliente",
    "email",
    "telefone",
    "endereco",
}


def _hash_value(value: Any) -> str:
    """SHA-256 truncado nos primeiros 12 chars — irreversível."""
    raw = str(value).encode("utf-8")
    return "***" + hashlib.sha256(raw).hexdigest()[:8]


def _bucket_score(value: float, buckets: list[tuple[float, str]]) -> str:
    """Converte score numérico em bucket categórico."""
    for threshold, label in sorted(buckets, key=lambda x: x[0]):
        if value <= threshold:
            return label
    return buckets[-1][1]


def apply_masking(
    rows: list[dict[str, Any]],
    sensitive_fields: set[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Aplica masking em todos os campos sensíveis de uma lista de rows.

    Args:
        rows: Lista de dicionários (resultado de query SQL)
        sensitive_fields: Conjunto de campos a mascarar.
                          Se None, usa DEFAULT_SENSITIVE_FIELDS.

    Returns:
        Lista de rows com campos sensíveis mascarados.
        Adiciona '_masked_fields' indicando quais campos foram mascarados.
    """
    fields_to_mask = sensitive_fields if sensitive_fields is not None else DEFAULT_SENSITIVE_FIELDS

    masked_rows = []
    for row in rows:
        new_row = dict(row)
        masked = []

        for field_name in list(new_row.keys()):
            # Checa se o campo (ou algum sufixo dele) é sensível
            if any(
                field_name == sf or field_name.endswith(f"_{sf}") or field_name.startswith(f"{sf}_")
                for sf in fields_to_mask
            ):
                original = new_row[field_name]
                if original is not None:
                    new_row[field_name] = _hash_value(original)
                    masked.append(field_name)

        new_row["_masked_fields"] = masked if masked else None
        masked_rows.append(new_row)

    return masked_rows


def get_sensitive_fields_in_result(
    rows: list[dict[str, Any]],
    sensitive_fields: set[str] | None = None,
) -> set[str]:
    """Retorna quais campos sensíveis estão presentes no resultado."""
    if not rows:
        return set()

    fields_to_check = sensitive_fields or DEFAULT_SENSITIVE_FIELDS
    result_fields = set(rows[0].keys())

    return {
        field
        for field in result_fields
        for sf in fields_to_check
        if field == sf or field.endswith(f"_{sf}") or field.startswith(f"{sf}_")
    }
