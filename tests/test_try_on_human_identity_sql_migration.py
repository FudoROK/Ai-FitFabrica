from __future__ import annotations

from pathlib import Path


def test_human_identity_analysis_migration_is_chained_after_agent_ledger() -> None:
    text = Path("alembic/versions/20260614_000012_try_on_human_identity_analysis.py").read_text(encoding="utf-8")

    assert 'revision = "20260614_000012"' in text
    assert 'down_revision = "20260614_000011"' in text
    assert '"try_on_human_identity_analyses"' in text
    assert '"try_on_jobs.job_id"' in text
    assert 'ondelete="CASCADE"' in text
