"""Tests for the workspace history route wiring."""
from __future__ import annotations

from pathlib import Path


def test_workspace_history_page_reads_recent_jobs_from_runtime_bootstrap() -> None:
    """The history page must use backend-owned recent_jobs instead of a static placeholder-only layout."""
    page_source = Path("apps/web/src/app/(workspace)/workspace/history/page.tsx").read_text(encoding="utf-8")

    assert "useWorkspaceRuntime" in page_source
    assert "bootstrap.recent_jobs" in page_source
    assert 'href="/workspace/new-fitting"' in page_source
