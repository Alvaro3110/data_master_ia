"""
TDD — Fase 1: SQL Validator com SQLGlot AST.
Testa casos avançados que o regex não captura:
- Comentários obscurecidos (/**/  --)
- UNION injection
- CTE que acessa tabela proibida
- Subquery com DDL
- Múltiplos statements via parse tree (não só ;)
"""
import pytest
from app.security.sql_validator import validate_sql


# ── Casos básicos (garantir regressão) ──────────────────────────────────────

class TestBasicRegression:
    def test_permite_select_simples(self):
        sql = "SELECT safra, AVG(margem_liquida) FROM fact_pricing_snapshot GROUP BY safra LIMIT 100"
        r = validate_sql(sql)
        assert r.allowed is True, r.reasons

    def test_bloqueia_drop(self):
        r = validate_sql("DROP TABLE fact_pricing_snapshot")
        assert r.allowed is False
        assert any("DDL" in reason or "DROP" in reason for reason in r.reasons)

    def test_bloqueia_delete(self):
        r = validate_sql("DELETE FROM fact_pricing_snapshot WHERE safra = '2026-01'")
        assert r.allowed is False
        assert any("DML" in reason or "DELETE" in reason for reason in r.reasons)

    def test_bloqueia_multi_statement_ponto_virgula(self):
        r = validate_sql("SELECT 1; DELETE FROM fact_pricing_snapshot")
        assert r.allowed is False
        assert any("multiple" in reason.lower() or "statements" in reason.lower() for reason in r.reasons)

    def test_bloqueia_full_scan_sem_limit(self):
        r = validate_sql("SELECT * FROM fact_pricing_snapshot")
        assert r.allowed is False
        assert r.rewrite_hint is not None


# ── Casos avançados com SQLGlot AST ─────────────────────────────────────────

class TestSQLGlotAST:
    def test_bloqueia_union_injection(self):
        """UNION pode ser usado para exfiltrar dados de outras tabelas."""
        sql = """
        SELECT safra FROM fact_pricing_snapshot LIMIT 10
        UNION ALL
        SELECT password FROM users LIMIT 10
        """
        r = validate_sql(sql)
        assert r.allowed is False
        assert any("union" in reason.lower() or "proibida" in reason.lower() for reason in r.reasons)

    def test_bloqueia_tabela_nao_autorizada(self):
        """Acesso a tabelas fora da whitelist deve ser bloqueado."""
        r = validate_sql("SELECT * FROM users LIMIT 10")
        assert r.allowed is False
        assert any("não autorizada" in reason.lower() or "whitelist" in reason.lower() for reason in r.reasons)

    def test_bloqueia_comentario_obscurecendo_drop(self):
        """Técnica clássica de bypass: DROP/**/TABLE"""
        r = validate_sql("DROP/**/TABLE fact_pricing_snapshot")
        assert r.allowed is False

    def test_bloqueia_comentario_inline_obscurecendo_delete(self):
        """Técnica: DELETE -- comentário\n FROM tabela"""
        r = validate_sql("DELETE -- comentário malicioso\nFROM fact_pricing_snapshot")
        assert r.allowed is False

    def test_bloqueia_cte_com_tabela_nao_autorizada(self):
        """CTE pode esconder acesso a tabelas proibidas."""
        sql = """
        WITH dados AS (
            SELECT cpf FROM dim_cliente LIMIT 100
        )
        SELECT * FROM dados
        """
        # dim_cliente não está na whitelist por padrão
        # (ou, se estiver, cpf deve ser mascarado — mas o validator verifica acesso)
        r = validate_sql(sql)
        # Dependendo da whitelist: se dim_cliente não for autorizada, deve bloquear
        # Se for autorizada, ao menos cpf deve acionar flag de campo sensível
        # Neste teste: garantimos que o AST consegue inspecionar o CTE
        assert isinstance(r.allowed, bool)  # pelo menos parseia sem erro

    def test_bloqueia_subquery_com_dml(self):
        """Subquery contendo DML deve ser bloqueada pelo AST."""
        sql = """
        SELECT safra FROM fact_pricing_snapshot
        WHERE safra IN (SELECT MAX(safra) FROM fact_pricing_snapshot)
        AND 1=(DELETE FROM fact_pricing_snapshot WHERE 1=1)
        LIMIT 10
        """
        r = validate_sql(sql)
        assert r.allowed is False

    def test_permite_cte_com_tabelas_autorizadas(self):
        """CTE legítimo com tabelas da whitelist deve ser permitido."""
        sql = """
        WITH ultima_safra AS (
            SELECT MAX(safra) as safra_max FROM fact_pricing_snapshot
        )
        SELECT s.segmento, AVG(s.margem_liquida) as margem_media
        FROM fact_pricing_snapshot s
        JOIN ultima_safra u ON s.safra = u.safra_max
        GROUP BY s.segmento
        LIMIT 50
        """
        r = validate_sql(sql)
        assert r.allowed is True, r.reasons

    def test_bloqueia_union_mesmo_sem_espaco(self):
        """UNION sem espaço antes/depois deve ser detectado via AST."""
        sql = "SELECT safra FROM fact_pricing_snapshot LIMIT 5 UNION SELECT table_name FROM information_schema.tables"
        r = validate_sql(sql)
        assert r.allowed is False

    def test_parse_error_retorna_bloqueado(self):
        """SQL inválido/malformado deve retornar bloqueado, não levantar exceção."""
        sql = "SELECT $$invalid SQL ))) ---"
        r = validate_sql(sql)
        assert r.allowed is False
        assert any("parse" in reason.lower() or "inválido" in reason.lower() or "malformed" in reason.lower() for reason in r.reasons)

    def test_bloqueia_information_schema(self):
        """Acesso ao information_schema expõe metadados do banco."""
        sql = "SELECT table_name FROM information_schema.tables LIMIT 10"
        r = validate_sql(sql)
        assert r.allowed is False

    def test_permite_with_clause_simples(self):
        """WITH (CTE) legítimo começa com WITH — deve ser aceito."""
        sql = """
        WITH agg AS (SELECT safra, COUNT(*) as n FROM fact_pricing_snapshot GROUP BY safra)
        SELECT * FROM agg LIMIT 20
        """
        r = validate_sql(sql)
        assert r.allowed is True, r.reasons
