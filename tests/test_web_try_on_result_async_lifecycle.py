"""Guardrails for Try-On result async lifecycle UX."""
from __future__ import annotations

from pathlib import Path


RESULT_VIEW = Path("apps/web/src/features/workspace/try-on-result.tsx")


def test_try_on_result_view_polls_status_without_full_page_reload() -> None:
    """The result screen must support async jobs without forcing browser reloads."""
    source = RESULT_VIEW.read_text(encoding="utf-8")

    assert "window.location.reload" not in source
    assert ".getJobStatus(" in source
    assert "setTimeout(" in source
    assert "clearTimeout(" in source
    assert "current_status" in source
    assert 'status === "failed"' in source
