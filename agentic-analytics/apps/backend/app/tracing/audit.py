"""
Audit log — persiste trace_id, SQL, latência e mascaramentos.
Usa DuckDB (dev) como fallback simples se PostgreSQL indisponível.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings


def persist_audit_log(
    trace_id: str,
    question: str,
    routed_path: str,
    sql_final: str | None,
    status: str,
    latency_ms: int,
    masked_fields: list[str] | None = None,
    session_id: str | None = None,
) -> None:
    """
    Persiste uma entrada no audit log.
    Tenta PostgreSQL primeiro; fallback para DuckDB local.
    """
    entry = {
        "audit_id": str(uuid.uuid4()),
        "trace_id": trace_id,
        "session_id": session_id or "anon",
        "question": question[:2000],
        "routed_path": routed_path,
        "sql_final": (sql_final or "")[:5000],
        "status": status,
        "latency_ms": latency_ms,
        "masked_fields": json.dumps(masked_fields or []),
        "created_at": datetime.utcnow().isoformat(),
    }

    # Tenta PostgreSQL
    try:
        _persist_postgres(entry)
        return
    except Exception:
        pass

    # Fallback: DuckDB / JSONL local
    try:
        _persist_duckdb(entry)
    except Exception as e:
        # Último fallback: arquivo JSONL
        _persist_jsonl(entry)


def _persist_postgres(entry: dict) -> None:
    import psycopg
    with psycopg.connect(settings.POSTGRES_URL.replace("+psycopg2", "")) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO query_audit_log
                    (trace_id, session_id, question, routed_path, sql_final,
                     status, latency_ms, masked_fields, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry["trace_id"], entry["session_id"], entry["question"],
                    entry["routed_path"], entry["sql_final"], entry["status"],
                    entry["latency_ms"], entry["masked_fields"], entry["created_at"],
                ),
            )
        conn.commit()


def _persist_duckdb(entry: dict) -> None:
    import duckdb
    db_path = Path(settings.DUCKDB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_audit_log (
                audit_id VARCHAR, trace_id VARCHAR, session_id VARCHAR,
                question TEXT, routed_path VARCHAR, sql_final TEXT,
                status VARCHAR, latency_ms INTEGER, masked_fields TEXT,
                created_at VARCHAR
            )
        """)
        conn.execute(
            "INSERT INTO query_audit_log VALUES (?,?,?,?,?,?,?,?,?,?)",
            list(entry.values()),
        )


def _persist_jsonl(entry: dict) -> None:
    log_path = Path("./logs/audit.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
