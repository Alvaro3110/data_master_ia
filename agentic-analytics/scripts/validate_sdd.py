#!/usr/bin/env python3
"""Validador de estrutura e contratos SDD."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SDD_DIR = PROJECT_ROOT / "docs" / "sdd"

REQUIRED_DOCS: dict[str, list[str]] = {
    "PRD.md": ["# Objetivo", "## Contexto de Negócio", "## Público-Alvo", "## Escopo MVP"],
    "SPEC.md": ["# Objetivo", "## Stack Técnica", "## Arquitetura de Referência"],
    "TASKS.md": ["# Objetivo", "## Vertical Slices"],
    "ACCEPTANCE_CRITERIA.md": ["# Objetivo", "## Critérios de Aceite"],
    "TEST_PLAN.md": ["# Objetivo", "## Estratégia de Testes", "live_openai"],
    "ARCHITECTURE.md": ["# Objetivo", "## Diagrama de Alto Nível", "```mermaid"],
    "API_CONTRACTS.md": ["# Objetivo", "## Envelope Padrão", "trace_id"],
    "DATA_CONTRACTS.md": ["# Objetivo", "## Workspace", "## Política de PII"],
    "SECURITY.md": ["# Objetivo", "## Validador SQL", "## Segredos e Configuração"],
    "OBSERVABILITY.md": ["# Objetivo", "## Trace ID", "## Métricas"],
    "PHASE_3_PLAN.md": ["# Objetivo", "## Evolução Proposta"],
    "QUESTIONS.md": ["# Objetivo", "## Questões em Aberto"],
}

REQUIRED_EXTRA_FILES: dict[str, list[str]] = {
    "AGENTS.md": ["# Mission", "## Responsibilities", "## Constraints", "## Workflow"],
}
COPILOT_FILE = PROJECT_ROOT.parent / ".github" / "copilot-instructions.md"
COPILOT_SNIPPETS = ["# Copilot Instructions", "docs/sdd", "{trace_id, data}"]

PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|lorem ipsum)\b|<\.\.\.>", re.IGNORECASE)
TASK_RE = re.compile(r"^- \[ \] VS\d{2}: .+ - Critério de aceite: .+$")
AC_RE = re.compile(r"^- AC\d{2}: .+$")
QUESTION_RE = re.compile(r"^- Q\d{2}: .+$")
JSON_BLOCK_RE = re.compile(r"```json", re.IGNORECASE)
ZERO_SHA = "0000000000000000000000000000000000000000"

SEMANTIC_REQUIREMENTS: dict[Path, list[str]] = {
    SDD_DIR / "TEST_PLAN.md": ["pytest", "playwright", "live_openai"],
    SDD_DIR / "SECURITY.md": ["sqlglot", "CORS", "rate-limit"],
    SDD_DIR / "OBSERVABILITY.md": ["trace_id", "latência", "erro"],
    PROJECT_ROOT / "AGENTS.md": ["Não alterar arquivos fora do escopo", "docs/sdd"],
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate_file(path: Path, required_snippets: list[str], errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"MISSING_FILE: {path}")
        return

    content = _read(path)
    if not content.strip():
        errors.append(f"EMPTY_FILE: {path}")
        return

    if PLACEHOLDER_RE.search(content):
        errors.append(f"PLACEHOLDER_FOUND: {path}")

    if len(content.split()) < 25:
        errors.append(f"CONTENT_TOO_SHORT: {path}")

    if "# " not in content:
        errors.append(f"MISSING_H1: {path}")

    for snippet in required_snippets:
        if snippet not in content:
            errors.append(f"MISSING_SNIPPET: {path} -> {snippet}")


def _validate_tasks(errors: list[str]) -> None:
    path = SDD_DIR / "TASKS.md"
    if not path.exists():
        return
    lines = [line.rstrip() for line in _read(path).splitlines() if line.strip().startswith("- [ ]")]
    if not lines:
        errors.append("TASKS_FORMAT: TASKS.md sem itens VS")
        return
    for line in lines:
        if not TASK_RE.match(line):
            errors.append(f"TASKS_FORMAT: linha inválida em TASKS.md -> {line}")


def _validate_acceptance(errors: list[str]) -> None:
    path = SDD_DIR / "ACCEPTANCE_CRITERIA.md"
    if not path.exists():
        return
    lines = [line.rstrip() for line in _read(path).splitlines() if line.strip().startswith("- AC")]
    if not lines:
        errors.append("AC_FORMAT: ACCEPTANCE_CRITERIA.md sem itens AC")
        return
    for line in lines:
        if not AC_RE.match(line):
            errors.append(f"AC_FORMAT: linha inválida em ACCEPTANCE_CRITERIA.md -> {line}")


def _validate_questions(errors: list[str]) -> None:
    path = SDD_DIR / "QUESTIONS.md"
    if not path.exists():
        return
    lines = [line.rstrip() for line in _read(path).splitlines() if line.strip().startswith("- Q")]
    if not lines:
        errors.append("QUESTIONS_FORMAT: QUESTIONS.md sem itens Q")
        return
    for line in lines:
        if not QUESTION_RE.match(line):
            errors.append(f"QUESTIONS_FORMAT: linha inválida em QUESTIONS.md -> {line}")


def _validate_architecture(errors: list[str]) -> None:
    path = SDD_DIR / "ARCHITECTURE.md"
    if not path.exists():
        return
    content = _read(path)
    if "```mermaid" not in content:
        errors.append("ARCHITECTURE_FORMAT: ARCHITECTURE.md sem bloco mermaid")


def _validate_api_contracts(errors: list[str]) -> None:
    path = SDD_DIR / "API_CONTRACTS.md"
    if not path.exists():
        return
    content = _read(path)
    json_blocks = len(JSON_BLOCK_RE.findall(content))
    if json_blocks < 2:
        errors.append("API_CONTRACTS_FORMAT: esperado no mínimo 2 exemplos JSON em API_CONTRACTS.md")
    lowered = content.lower()
    if '"trace_id"' not in lowered or '"data"' not in lowered:
        errors.append("API_CONTRACTS_FORMAT: exemplos JSON devem explicitar campos trace_id e data")


def _validate_semantics(errors: list[str]) -> None:
    for path, snippets in SEMANTIC_REQUIREMENTS.items():
        if not path.exists():
            continue
        content = _read(path).lower()
        for snippet in snippets:
            if snippet.lower() not in content:
                errors.append(f"SEMANTIC_MISSING: {path} -> {snippet}")


def _run_git_diff(diff_range: str | None = None) -> tuple[list[str], bool]:
    if diff_range and ZERO_SHA in diff_range:
        diff_range = None

    cmd: list[str]
    if diff_range:
        cmd = ["git", "diff", "--name-only", diff_range]
    else:
        base_ref = os.getenv("GITHUB_BASE_REF", "").strip()
        github_before = os.getenv("GITHUB_EVENT_BEFORE", "").strip()
        if base_ref:
            cmd = ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]
        elif github_before and github_before != "0000000000000000000000000000000000000000":
            cmd = ["git", "diff", "--name-only", f"{github_before}..HEAD"]
        else:
            cmd = ["git", "diff", "--name-only", "HEAD~1..HEAD"]

    commands = [
        cmd,
        ["git", "diff", "--name-only"],
    ]

    for diff_cmd in commands:
        try:
            output = subprocess.check_output(diff_cmd, cwd=PROJECT_ROOT.parent, text=True)
            files = [line.strip() for line in output.splitlines() if line.strip()]
            return files, True
        except Exception:
            continue

    return [], False


def check_diff_gate(changed_files: list[str]) -> list[str]:
    errors: list[str] = []
    code_changed = any(path.startswith("agentic-analytics/apps/") for path in changed_files)
    sdd_changed = any(path.startswith("agentic-analytics/docs/sdd/") for path in changed_files)

    if code_changed and not sdd_changed:
        errors.append(
            "DIFF_GATE: mudanças em agentic-analytics/apps/** exigem atualização em agentic-analytics/docs/sdd/**"
        )
    return errors


def validate(check_diff: bool = False, diff_range: str | None = None) -> list[str]:
    errors: list[str] = []

    for file_name, snippets in REQUIRED_DOCS.items():
        _validate_file(SDD_DIR / file_name, snippets, errors)

    for file_name, snippets in REQUIRED_EXTRA_FILES.items():
        _validate_file(PROJECT_ROOT / file_name, snippets, errors)

    _validate_file(COPILOT_FILE, COPILOT_SNIPPETS, errors)

    _validate_tasks(errors)
    _validate_acceptance(errors)
    _validate_questions(errors)
    _validate_architecture(errors)
    _validate_api_contracts(errors)
    _validate_semantics(errors)

    if check_diff:
        changed_files, diff_resolved = _run_git_diff(diff_range=diff_range)
        if not diff_resolved:
            errors.append("DIFF_GATE_UNRESOLVED: não foi possível calcular git diff com segurança")
        elif os.getenv("CI", "").lower() == "true" and not changed_files:
            errors.append("DIFF_GATE_UNRESOLVED: git diff vazio em CI; impossível validar gate de contrato")
        errors.extend(check_diff_gate(changed_files))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida estrutura e contratos SDD")
    parser.add_argument("--check-diff", action="store_true", help="Exige mudança em docs/sdd quando apps/** mudar")
    parser.add_argument("--diff-range", type=str, default=None, help="Range explícito para git diff (opcional)")
    args = parser.parse_args()

    errors = validate(check_diff=args.check_diff, diff_range=args.diff_range)
    if errors:
        for err in errors:
            print(err)
        return 1

    print("SDD validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
