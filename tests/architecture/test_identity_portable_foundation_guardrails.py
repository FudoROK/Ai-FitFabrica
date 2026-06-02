"""Architecture guardrails for portable SQL identity components."""

from __future__ import annotations

from pathlib import Path


def test_identity_sql_runtime_code_does_not_import_firestore() -> None:
    """Portable SQL identity code must not depend on Firestore runtime adapters."""
    root = Path(__file__).resolve().parents[2]
    for file_path in [
        root / "src" / "adapters" / "database" / "sql" / "identity_models.py",
        root / "src" / "adapters" / "database" / "sql" / "identity_repositories.py",
        root / "src" / "adapters" / "database" / "sql" / "identity_audit.py",
    ]:
        text = file_path.read_text(encoding="utf-8").lower()
        assert "firestore" not in text
