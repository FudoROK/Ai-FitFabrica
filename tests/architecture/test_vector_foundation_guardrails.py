"""Guardrails for the portable vector foundation."""

from __future__ import annotations

from pathlib import Path


def test_vector_foundation_does_not_depend_on_google_managed_search() -> None:
    """Vector code must not drift toward Google-managed search assumptions."""
    root = Path("src/adapters/vector")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "vertex ai search" not in text
        assert "discoveryengine" not in text
