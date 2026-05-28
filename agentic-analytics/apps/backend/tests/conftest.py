from __future__ import annotations

import os
from pathlib import Path

import pytest


def _test_db_mode() -> str:
    return os.getenv("TEST_DB_MODE", "auto").strip().lower()


def _configure_test_db_url() -> None:
    if os.getenv("POSTGRES_URL"):
        return

    mode = _test_db_mode()
    if mode in {"auto", "sqlite"}:
        sqlite_path = Path(os.getenv("TEST_SQLITE_PATH", "/tmp/agentic_analytics_tests.db")).resolve()
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        os.environ["POSTGRES_URL"] = f"sqlite+pysqlite:///{sqlite_path}"


_configure_test_db_url()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live_openai: Mark test as requiring live OpenAI API credentials"
    )


@pytest.fixture(autouse=True)
def reset_workspace_db():
    from app.api.v1.workspaces import db

    try:
        db.reset()
    except Exception as exc:
        mode = _test_db_mode()
        if mode in {"skip", "skip_if_unavailable"}:
            pytest.skip(f"Banco indisponível para testes (mode={mode}): {exc}")
        raise RuntimeError(
            "TEST_DB_RESET_FAILED: não foi possível resetar o banco de testes. "
            "Defina POSTGRES_URL válido ou use TEST_DB_MODE=sqlite/auto para fallback local."
        ) from exc
