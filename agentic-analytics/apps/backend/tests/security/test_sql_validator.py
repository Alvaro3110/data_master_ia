# apps/backend/tests/security/test_sql_validator.py
from app.security.sql_validator import validate_sql


def test_bloqueia_dml_delete():
    result = validate_sql("DELETE FROM fact_pricing_snapshot")
    assert result.allowed is False
    assert any("DML" in reason or "DELETE" in reason for reason in result.reasons)


def test_bloqueia_dml_insert():
    result = validate_sql(
        "INSERT INTO fact_pricing_snapshot (safra) VALUES ('2026-03')"
    )
    assert result.allowed is False
    assert any("DML" in reason or "INSERT" in reason for reason in result.reasons)


def test_bloqueia_ddl_drop():
    result = validate_sql("DROP TABLE fact_pricing_snapshot")
    assert result.allowed is False
    assert any("DDL" in reason or "DROP" in reason for reason in result.reasons)


def test_bloqueia_ddl_alter():
    result = validate_sql("ALTER TABLE fact_pricing_snapshot ADD COLUMN test_col TEXT")
    assert result.allowed is False
    assert any("DDL" in reason or "ALTER" in reason for reason in result.reasons)


def test_bloqueia_ddl_create():
    result = validate_sql("CREATE TABLE my_table (id INT)")
    assert result.allowed is False
    assert any("DDL" in reason or "CREATE" in reason for reason in result.reasons)
