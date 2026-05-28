from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDD_DIR = ROOT / "docs" / "sdd"
WORKFLOW = ROOT.parent / ".github" / "workflows" / "sdd-validation.yml"
VALIDATOR_PATH = ROOT / "scripts" / "validate_sdd.py"


def _load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_sdd", VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vs_references_existing_acceptance_ids() -> None:
    tasks_text = (SDD_DIR / "TASKS.md").read_text(encoding="utf-8")
    ac_text = (SDD_DIR / "ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8")

    defined_acs = set(re.findall(r"\bAC\d{2}\b", ac_text))
    assert defined_acs, "ACCEPTANCE_CRITERIA.md deve definir IDs ACxx"

    vs_lines = [line for line in tasks_text.splitlines() if line.strip().startswith("- [ ] VS")]
    assert vs_lines, "TASKS.md deve conter itens VS"

    for line in vs_lines:
        refs = set(re.findall(r"\bAC\d{2}\b", line))
        assert refs, f"VS sem referência AC: {line}"
        missing = refs - defined_acs
        assert not missing, f"VS referencia AC inexistente: {missing} em '{line}'"


def test_test_plan_mentions_live_openai_policy() -> None:
    text = (SDD_DIR / "TEST_PLAN.md").read_text(encoding="utf-8")
    assert "live_openai" in text
    assert "não podem chamar OpenAI real" in text or "não podem" in text


def test_workflow_has_expected_validation_steps() -> None:
    assert WORKFLOW.exists(), "Workflow sdd-validation.yml deve existir"
    content = WORKFLOW.read_text(encoding="utf-8")
    assert "python agentic-analytics/scripts/validate_sdd.py --check-diff" in content
    assert "pytest -q agentic-analytics/tests/test_sdd_*.py" in content
    assert "markdownlint" in content


def test_diff_gate_requires_docs_when_apps_change() -> None:
    mod = _load_validator_module()
    errors = mod.check_diff_gate(["agentic-analytics/apps/backend/app/main.py"])
    assert errors, "Diff gate deve falhar se apps/** muda sem docs/sdd/**"


def test_diff_gate_passes_when_apps_and_sdd_change() -> None:
    mod = _load_validator_module()
    errors = mod.check_diff_gate([
        "agentic-analytics/apps/backend/app/main.py",
        "agentic-analytics/docs/sdd/SPEC.md",
    ])
    assert not errors
