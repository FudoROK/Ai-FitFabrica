"""Guardrails for owner-facing readiness documents."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OWNER_DOC = PROJECT_ROOT / "docs" / "04_OWNER_REMAINING_WORK.md"
DOCS_INDEX = PROJECT_ROOT / "docs" / "README.md"
TESTS_DOC = PROJECT_ROOT / "docs" / "tests_description.md"


def _read(path: Path) -> str:
    """Read one documentation file as UTF-8 text."""

    return path.read_text(encoding="utf-8")


def test_owner_status_doc_uses_current_readiness_baseline() -> None:
    """Owner document must point to the current pre-billing readiness truth."""

    text = _read(OWNER_DOC)

    assert "Дата актуализации: 2026-07-08" in text
    assert "1205 passed" in text
    assert "scripts/no_billing_acceptance_gate.py --full-backend --skip-frontend-build" in text
    assert "scripts/web_dependency_audit.py --require-ready" in text
    assert "scripts/post_billing_acceptance_gate.py" in text
    assert "рабочее дерево чистое" in text


def test_owner_facing_docs_do_not_reference_stale_readiness_counts() -> None:
    """Current owner-facing docs should not keep obsolete verification numbers."""

    combined = "\n".join(_read(path) for path in (OWNER_DOC, DOCS_INDEX, TESTS_DOC))

    stale_fragments = (
        "1129 passed",
        "1141 passed",
        "1186 passed",
        "1192 passed",
        "1195 passed",
        "1198 passed",
        "1201 passed",
        "1202 passed",
        "1203 passed",
        "грязным",
        "dirty working tree",
        "Дата актуализации: 2026-06-17",
    )
    for fragment in stale_fragments:
        assert fragment not in combined


def test_tests_description_lists_acceptance_gate_commands() -> None:
    """Tests documentation must describe the current acceptance gates."""

    text = _read(TESTS_DOC)

    assert "scripts/no_billing_acceptance_gate.py" in text
    assert "scripts/web_dependency_audit.py --require-ready" in text
    assert "1205 passed" in text
