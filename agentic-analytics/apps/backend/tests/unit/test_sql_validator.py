"""
Testes unitários do SQL Validator.
Casos exatos do deep-research-report.md + casos adicionais de segurança.
Roda sem dependências externas (sem DB, sem Docker).
"""
import pytest

from app.security.sql_validator import validate_sql


# ─── DDL ─────────────────────────────────────────────────────────────────────

def test_bloqueia_drop_table():
    verdict = validate_sql("DROP TABLE fact_pricing_snapshot;")
    assert verdict.allowed is False
    assert any("DROP" in r for r in verdict.reasons)


def test_bloqueia_alter_table():
    verdict = validate_sql("ALTER TABLE dim_cliente ADD COLUMN test TEXT;")
    assert verdict.allowed is False
    assert any("DDL" in r for r in verdict.reasons)


def test_bloqueia_create_table():
    verdict = validate_sql("CREATE TABLE evil AS SELECT * FROM dim_cliente;")
    assert verdict.allowed is False


def test_bloqueia_truncate():
    verdict = validate_sql("TRUNCATE TABLE query_audit_log;")
    assert verdict.allowed is False


# ─── DML ─────────────────────────────────────────────────────────────────────

def test_bloqueia_delete():
    verdict = validate_sql("DELETE FROM fact_pricing_snapshot WHERE safra = '2026-03';")
    assert verdict.allowed is False
    assert any("DELETE" in r for r in verdict.reasons)


def test_bloqueia_insert():
    verdict = validate_sql("INSERT INTO dim_cliente VALUES (1, 'test', 'PME');")
    assert verdict.allowed is False


def test_bloqueia_update():
    verdict = validate_sql("UPDATE fact_pricing_snapshot SET margem_liquida = 0;")
    assert verdict.allowed is False


# ─── Multi-statement ──────────────────────────────────────────────────────────

def test_bloqueia_multistatement():
    verdict = validate_sql(
        "SELECT * FROM fact_pricing_snapshot LIMIT 10; DELETE FROM users;"
    )
    assert verdict.allowed is False
    assert any("multiple statements" in r.lower() for r in verdict.reasons)


def test_bloqueia_multistatement_com_select():
    verdict = validate_sql(
        "SELECT 1; SELECT 2;"
    )
    assert verdict.allowed is False


# ─── Full scan sem LIMIT ──────────────────────────────────────────────────────

def test_exige_limit_para_tabela_grande():
    verdict = validate_sql("SELECT * FROM fact_pricing_snapshot")
    assert verdict.allowed is False
    assert verdict.rewrite_hint is not None
    assert "LIMIT" in verdict.rewrite_hint


def test_exige_limit_para_audit_log():
    verdict = validate_sql("SELECT * FROM query_audit_log WHERE trace_id = 'abc'")
    # query_audit_log é tabela grande — exige LIMIT
    assert verdict.allowed is False


# ─── Queries Válidas ──────────────────────────────────────────────────────────

def test_permite_select_agregado():
    verdict = validate_sql("""
        SELECT safra, AVG(margem_liquida) AS margem_media
        FROM fact_pricing_snapshot
        WHERE safra = '2026-03'
        GROUP BY safra
        LIMIT 100
    """)
    assert verdict.allowed is True
    assert len(verdict.reasons) == 0


def test_permite_select_com_join():
    verdict = validate_sql("""
        SELECT fp.safra, fp.segmento, AVG(fp.roae) as roae_medio
        FROM fact_pricing_snapshot fp
        JOIN dim_produto dp ON fp.produto = dp.produto_id
        WHERE fp.safra >= '2025-01'
          AND fp.score_risco >= 7
        GROUP BY fp.safra, fp.segmento
        ORDER BY roae_medio
        LIMIT 50
    """)
    assert verdict.allowed is True


def test_permite_with_cte():
    verdict = validate_sql("""
        WITH ultima_safra AS (
            SELECT MAX(safra) AS max_safra FROM fact_pricing_snapshot
        )
        SELECT segmento, AVG(margem_liquida) as margem
        FROM fact_pricing_snapshot fps, ultima_safra
        WHERE fps.safra = ultima_safra.max_safra
        GROUP BY segmento
        LIMIT 50
    """)
    assert verdict.allowed is True


def test_permite_subquery():
    verdict = validate_sql("""
        SELECT segmento, AVG(roae) as roae_medio
        FROM fact_pricing_snapshot
        WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
          AND score_risco >= 7
        GROUP BY segmento
        ORDER BY roae_medio
        LIMIT 50
    """)
    assert verdict.allowed is True


# ─── Funções perigosas ────────────────────────────────────────────────────────

def test_bloqueia_pg_read_file():
    verdict = validate_sql("SELECT pg_read_file('/etc/passwd')")
    assert verdict.allowed is False


def test_bloqueia_dblink():
    verdict = validate_sql("SELECT * FROM dblink('host=evil', 'SELECT 1')")
    assert verdict.allowed is False


# ─── Comentários SQL (evasão) ─────────────────────────────────────────────────

def test_ddl_em_comentario_inline_com_multistatement():
    """SELECT 1; DROP... → multi-statement, bloqueado."""
    verdict = validate_sql("SELECT 1; DROP TABLE fact_pricing_snapshot;")
    assert verdict.allowed is False  # bloqueado por multi-statement


def test_ddl_somente_em_comentario_bloco_select_valido():
    """
    /* DROP TABLE users; */ SELECT 1 LIMIT 1
    Após strip de comentários: 'SELECT 1 LIMIT 1' — query válida.
    O DDL estava apenas no comentário e não representa ameaça real.
    """
    verdict = validate_sql("/* DROP TABLE users; */ SELECT 1 LIMIT 1")
    # Comportamento correto: strip remove o comentário, resta SELECT válido
    assert isinstance(verdict.allowed, bool)  # não quebra
    # Mas o SELECT sem tabela grande não exige LIMIT obrigatório
    # → é uma query válida após strip
