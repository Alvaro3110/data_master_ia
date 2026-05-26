"""
Testes unitários do módulo de Masking.
Verifica que campos PII são mascarados e valores não-sensíveis preservados.
"""
import pytest

from app.security.masking import apply_masking, get_sensitive_fields_in_result


def test_mascaramento_cliente_id():
    rows = [{"cliente_id": "12345678900", "margem_liquida": 10.5}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert masked[0]["cliente_id"] != "12345678900"
    assert masked[0]["cliente_id"].startswith("***")
    assert masked[0]["margem_liquida"] == 10.5


def test_preserva_campos_nao_sensiveis():
    rows = [{"safra": "2026-03", "segmento": "PME", "roae": 12.5}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert masked[0]["safra"] == "2026-03"
    assert masked[0]["segmento"] == "PME"
    assert masked[0]["roae"] == 12.5


def test_masking_multiplos_campos():
    rows = [{
        "cliente_id": "99999999900",
        "cpf": "000.000.000-00",
        "margem_liquida": 5.0,
        "safra": "2026-01",
    }]
    masked = apply_masking(rows, sensitive_fields={"cliente_id", "cpf"})
    assert masked[0]["cliente_id"] != "99999999900"
    assert masked[0]["cpf"] != "000.000.000-00"
    assert masked[0]["margem_liquida"] == 5.0
    assert masked[0]["safra"] == "2026-01"


def test_masked_fields_registrado():
    rows = [{"cliente_id": "abc123", "roae": 8.0}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert "cliente_id" in masked[0]["_masked_fields"]


def test_sem_campos_sensiveis_masked_fields_none():
    rows = [{"safra": "2026-03", "margem_liquida": 10.0}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert masked[0]["_masked_fields"] is None


def test_hash_deterministico():
    """O mesmo valor deve sempre produzir o mesmo hash."""
    rows1 = [{"cliente_id": "12345678900"}]
    rows2 = [{"cliente_id": "12345678900"}]
    m1 = apply_masking(rows1, sensitive_fields={"cliente_id"})
    m2 = apply_masking(rows2, sensitive_fields={"cliente_id"})
    assert m1[0]["cliente_id"] == m2[0]["cliente_id"]


def test_hash_diferente_para_valores_diferentes():
    rows = [{"cliente_id": "111"}, {"cliente_id": "222"}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert masked[0]["cliente_id"] != masked[1]["cliente_id"]


def test_lista_vazia():
    assert apply_masking([], sensitive_fields={"cliente_id"}) == []


def test_valor_none_nao_mascara():
    rows = [{"cliente_id": None, "roae": 5.0}]
    masked = apply_masking(rows, sensitive_fields={"cliente_id"})
    assert masked[0]["cliente_id"] is None


def test_default_sensitive_fields():
    """Com sensitive_fields=None usa DEFAULT_SENSITIVE_FIELDS."""
    rows = [{"cliente_id": "abc", "cpf": "123", "roae": 1.0}]
    masked = apply_masking(rows)  # sem sensitive_fields explícito
    assert masked[0]["cliente_id"] != "abc"
    assert masked[0]["cpf"] != "123"
    assert masked[0]["roae"] == 1.0


def test_get_sensitive_fields_in_result():
    rows = [{"cliente_id": "x", "safra": "2026-03"}]
    found = get_sensitive_fields_in_result(rows, sensitive_fields={"cliente_id"})
    assert "cliente_id" in found
    assert "safra" not in found
