from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDD_DIR = ROOT / "docs" / "sdd"
VALIDATOR = ROOT / "scripts" / "validate_sdd.py"

REQUIRED_FILES = [
    "PRD.md",
    "SPEC.md",
    "TASKS.md",
    "ACCEPTANCE_CRITERIA.md",
    "TEST_PLAN.md",
    "ARCHITECTURE.md",
    "API_CONTRACTS.md",
    "DATA_CONTRACTS.md",
    "SECURITY.md",
    "OBSERVABILITY.md",
    "PHASE_3_PLAN.md",
    "QUESTIONS.md",
]


def test_required_sdd_files_exist() -> None:
    missing = [name for name in REQUIRED_FILES if not (SDD_DIR / name).exists()]
    assert not missing, f"Arquivos SDD ausentes: {missing}"


def test_agents_file_exists_with_required_sections() -> None:
    path = ROOT / "AGENTS.md"
    content = path.read_text(encoding="utf-8")
    assert "# Mission" in content
    assert "## Responsibilities" in content
    assert "## Constraints" in content
    assert "## Workflow" in content


def test_tasks_follow_vs_format() -> None:
    lines = [
        line.strip()
        for line in (SDD_DIR / "TASKS.md").read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- [ ]")
    ]
    assert lines, "TASKS.md deve ter ao menos um item VS"
    pattern = re.compile(r"^- \[ \] VS\d{2}: .+ - Critério de aceite: .+$")
    invalid = [line for line in lines if not pattern.match(line)]
    assert not invalid, f"Linhas VS inválidas: {invalid}"


def test_questions_follow_q_format() -> None:
    lines = [
        line.strip()
        for line in (SDD_DIR / "QUESTIONS.md").read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- Q")
    ]
    assert lines, "QUESTIONS.md deve ter ao menos um item Q"
    pattern = re.compile(r"^- Q\d{2}: .+$")
    invalid = [line for line in lines if not pattern.match(line)]
    assert not invalid, f"Linhas Q inválidas: {invalid}"


def test_validator_cli_passes_default_mode() -> None:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SDD validation passed" in proc.stdout
