"""Architecture guardrails for portable infrastructure adapters."""

from __future__ import annotations

from pathlib import Path


def test_portable_foundation_packages_do_not_depend_on_google_storage_primitives() -> None:
    """Portable foundation packages must stay free of Google-specific persistence imports."""
    root = Path(__file__).resolve().parents[2]
    target_directories = [
        root / "src" / "adapters" / "database" / "sql",
        root / "src" / "adapters" / "cache",
        root / "src" / "adapters" / "storage",
        root / "src" / "adapters" / "vector",
    ]

    for directory in target_directories:
        for file_path in directory.rglob("*.py"):
            text = file_path.read_text(encoding="utf-8").lower()
            assert "google.cloud" not in text
            assert "firestore" not in text
            assert "gcs" not in text
