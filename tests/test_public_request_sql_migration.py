"""Guardrails for public request SQL persistence."""

from pathlib import Path


def test_public_demo_requests_have_sql_model_and_migration() -> None:
    model_source = Path("src/adapters/database/sql/public_request_models.py").read_text(encoding="utf-8")
    migration_source = Path("alembic/versions/20260703_000026_public_demo_requests.py").read_text(encoding="utf-8")

    assert "__tablename__ = \"public_demo_requests\"" in model_source
    assert "public_demo_requests" in migration_source
    assert "20260702_000025" in migration_source
