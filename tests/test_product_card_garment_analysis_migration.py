from pathlib import Path


def test_product_card_garment_analysis_migration_defines_one_to_one_table() -> None:
    source = Path("alembic/versions/20260615_000014_product_card_garment_analysis.py").read_text(encoding="utf-8")

    assert 'revision = "20260615_000014"' in source
    assert 'down_revision = "20260615_000013"' in source
    assert '"product_card_garment_analyses"' in source
    assert '["product_card_jobs.job_id"]' in source
