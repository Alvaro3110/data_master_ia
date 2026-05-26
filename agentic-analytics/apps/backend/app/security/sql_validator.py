"""
SQL Validator — camada de segurança crítica.
Bloqueia DDL, DML, multi-statement, full scan sem LIMIT.
Fase 1: SQLGlot AST para parsing robusto — elimina bypass via comentários,
UNION injection, tabelas não autorizadas e SQL malformado.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import sqlglot
import sqlglot.expressions as exp

# ── Configuração de whitelist ────────────────────────────────────────────────

# Tabelas autorizadas — acesso fora desta lista é bloqueado pelo AST
AUTHORIZED_TABLES: set[str] = {
    "fact_pricing_snapshot",
    "dim_cliente",
    "dim_produto",
    "metric_catalog",
    "schema_catalog",
    "semantic_rule_docs",
    "semantic_rule_chunks",
    "agent_sessions",
    "query_audit_log",
    "report_artifacts",
}

# Tabelas grandes que exigem LIMIT obrigatório
LARGE_TABLES: set[str] = {
    "fact_pricing_snapshot",
    "query_audit_log",
    "report_artifacts",
}

# Schemas/bancos proibidos (ex: metadados do banco)
BLOCKED_SCHEMAS: set[str] = {
    "information_schema",
    "pg_catalog",
    "sys",
    "mysql",
    "performance_schema",
}

# Tipos de statement DDL/DML bloqueados via AST
_BLOCKED_STATEMENT_TYPES = (
    exp.Drop, exp.Create, exp.Alter, exp.TruncateTable, exp.Insert,
    exp.Update, exp.Delete, exp.Merge, exp.Command,
)

# Funções perigosas — verificação léxica reforçada
_DANGEROUS_FUNCS = re.compile(
    r"\b(pg_read_file|lo_import|lo_export|dblink|pg_exec|system|cmd_exec|xp_cmdshell)\b",
    re.IGNORECASE,
)


# ── Modelo de resultado ──────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    rewrite_hint: str | None = None

    def __bool__(self) -> bool:
        return self.allowed


# ── Funções auxiliares ───────────────────────────────────────────────────────

def _extract_table_names(ast: exp.Expression) -> set[str]:
    """
    Extrai nomes de tabelas FÍSICAS do AST, excluindo aliases de CTE.
    CTEs definem aliases temporários (ex: WITH ultima_safra AS (...)) que não
    são tabelas físicas e não devem ser checados contra a whitelist.
    """
    # Coleta aliases de CTE — esses nomes são "virtuais"
    cte_aliases: set[str] = set()
    for node in ast.walk():
        if isinstance(node, exp.CTE):
            alias = node.args.get("alias")
            if alias:
                name = alias.name.lower() if hasattr(alias, "name") else str(alias).lower()
                cte_aliases.add(name)

    tables: set[str] = set()
    for node in ast.walk():
        if isinstance(node, exp.Table):
            db = node.args.get("db")
            table = node.name.lower() if node.name else ""
            schema = db.name.lower() if db and hasattr(db, "name") else ""

            # Ignora referências a aliases de CTE
            if table in cte_aliases:
                continue

            if schema:
                tables.add(f"{schema}.{table}")
            if table:
                tables.add(table)
    return tables


def _has_union(ast: exp.Expression) -> bool:
    """Detecta UNION/UNION ALL/INTERSECT/EXCEPT no AST."""
    for node in ast.walk():
        if isinstance(node, (exp.Union, exp.Intersect, exp.Except)):
            return True
    return False


def _has_limit(ast: exp.Expression) -> bool:
    """Verifica se existe cláusula LIMIT no AST."""
    for node in ast.walk():
        if isinstance(node, exp.Limit):
            return True
    return False


def _uses_large_table(tables: set[str]) -> str | None:
    """Retorna o nome da primeira tabela grande encontrada, ou None."""
    for t in tables:
        if t in LARGE_TABLES:
            return t
    return None


# ── Validador principal ──────────────────────────────────────────────────────

def validate_sql(sql: str) -> ValidationResult:
    """
    Valida uma query SQL usando SQLGlot AST (Fase 1) com fallback léxico.

    Retorna ValidationResult com:
    - allowed: True se a query é segura e autorizada
    - reasons: lista de motivos de bloqueio
    - rewrite_hint: sugestão de reformulação (se aplicável)
    """
    reasons: list[str] = []
    rewrite_hint: str | None = None

    # ── Guarda vazia ─────────────────────────────────────────────────────────
    if not sql or not sql.strip():
        return ValidationResult(allowed=False, reasons=["Query vazia."])

    # ── 1. Parse com SQLGlot ──────────────────────────────────────────────────
    try:
        statements = sqlglot.parse(sql, dialect="duckdb", error_level=sqlglot.ErrorLevel.RAISE)
    except Exception as e:
        return ValidationResult(
            allowed=False,
            reasons=[f"SQL malformed/parse error — query inválida: {e}"],
        )

    if not statements or statements[0] is None:
        return ValidationResult(allowed=False, reasons=["SQL vazio ou não reconhecido."])

    # ── 2. Multi-statement ────────────────────────────────────────────────────
    if len(statements) > 1:
        reasons.append("Multiple statements detected — only single SELECT allowed.")

    # ── 3. Verificar tipo de statement (DDL/DML/Admin) ────────────────────────
    for stmt in statements:
        if stmt is None:
            continue
        if isinstance(stmt, _BLOCKED_STATEMENT_TYPES):
            reasons.append(
                f"DDL/DML command detected: {type(stmt).__name__.upper()} — not allowed."
            )
        # Garantir que começa com SELECT ou WITH
        if not isinstance(stmt, (exp.Select, exp.With)):
            # Pode ser wrapped — checar o root
            is_select_root = any(
                isinstance(node, exp.Select) for node in stmt.walk()
                if node is stmt  # só o root
            )
            if not isinstance(stmt, (exp.Select, exp.With)) and not reasons:
                reasons.append(
                    f"Query must start with SELECT or WITH, got: {type(stmt).__name__.upper()}"
                )

    if reasons:
        return ValidationResult(allowed=False, reasons=reasons)

    # A partir daqui, trabalha com o primeiro statement
    ast = statements[0]

    # ── 4. UNION / INTERSECT / EXCEPT ────────────────────────────────────────
    if _has_union(ast):
        reasons.append(
            "UNION/INTERSECT/EXCEPT detected — set operations may expose unauthorized data."
        )

    # ── 5. Funções perigosas (léxico) ─────────────────────────────────────────
    if _DANGEROUS_FUNCS.search(sql):
        m = _DANGEROUS_FUNCS.search(sql)
        reasons.append(f"Dangerous function detected: {m.group()} — not allowed.")

    # ── 6. Tabelas autorizadas via AST ────────────────────────────────────────
    all_tables = _extract_table_names(ast)
    for table_ref in all_tables:
        # Checa schema bloqueado
        schema_part = table_ref.split(".")[0] if "." in table_ref else ""
        if schema_part in BLOCKED_SCHEMAS:
            reasons.append(
                f"Acesso bloqueado ao schema '{schema_part}' — não autorizado."
            )
            continue
        # Checa tabela na whitelist (ignora referências com schema já bloqueado)
        bare_name = table_ref.split(".")[-1]
        if bare_name not in AUTHORIZED_TABLES and schema_part not in BLOCKED_SCHEMAS:
            reasons.append(
                f"Tabela não autorizada na whitelist: '{bare_name}' — acesso negado."
            )

    # ── 7. Full scan em tabelas grandes sem LIMIT ─────────────────────────────
    if not reasons:
        large = _uses_large_table(all_tables)
        if large and not _has_limit(ast):
            reasons.append(
                f"Full scan on large table '{large}' without LIMIT — add LIMIT clause."
            )
            rewrite_hint = f"Add 'LIMIT 1000' to your query on '{large}'."

    return ValidationResult(
        allowed=len(reasons) == 0,
        reasons=reasons,
        rewrite_hint=rewrite_hint,
    )
