from pathlib import Path


def test_try_on_garment_slot_analysis_migration_exists() -> None:
    migration = Path("alembic/versions/20260623_000018_try_on_garment_slot_analysis.py").read_text(encoding="utf-8")

    assert 'revision = "20260623_000018"' in migration
    assert 'down_revision = "20260623_000017"' in migration
    assert '"try_on_garment_slot_identity_analyses"' in migration
    assert '"slot_role"' in migration
    assert '"uq_try_on_garment_slot_identity_job_role"' in migration
    assert '"ix_try_on_garment_slot_identity_job_position"' in migration
