from pathlib import Path


def test_try_on_analysis_bundle_migration_is_chained_after_product_card_analysis() -> None:
    text = Path("alembic/versions/20260615_000015_try_on_analysis_bundle.py").read_text(encoding="utf-8")

    assert 'revision = "20260615_000015"' in text
    assert 'down_revision = "20260615_000014"' in text
    assert '"try_on_garment_identity_analyses"' in text
    assert '"try_on_material_texture_analyses"' in text
