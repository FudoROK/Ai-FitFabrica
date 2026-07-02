from pathlib import Path


def test_garment_taxonomy_has_head_migration() -> None:
    migration = Path("alembic/versions/20260623_000017_garment_taxonomy.py").read_text(encoding="utf-8")

    assert 'revision = "20260623_000017"' in migration
    assert 'down_revision = "20260615_000016"' in migration
    for table_name in (
        "garment_taxonomy_items",
        "garment_wear_controls",
        "garment_taxonomy_candidates",
        "garment_taxonomy_audit_log",
    ):
        assert f'"{table_name}"' in migration

    for index_name in (
        "ix_garment_taxonomy_items_code",
        "ix_garment_wear_controls_control_code",
        "ix_garment_taxonomy_candidates_status",
        "ix_garment_taxonomy_audit_log_entity",
    ):
        assert f'"{index_name}"' in migration

    assert '"default_for_auto"' in migration


def test_baseline_wear_controls_seed_migration_is_reproducible() -> None:
    migration = Path("alembic/versions/20260624_000020_seed_baseline_garment_wear_controls.py").read_text(encoding="utf-8")

    assert 'revision = "20260624_000020"' in migration
    assert 'down_revision = "20260624_000019"' in migration
    for item_code in (
        "shirt",
        "t_shirt",
        "blouse",
        "hoodie",
        "jacket",
        "coat",
        "dress",
        "pants",
        "jeans",
        "skirt",
    ):
        assert f'"{item_code}"' in migration

    for control_code in (
        "auto",
        "untucked",
        "tucked",
        "open_front",
        "buttoned_closed",
        "high_waist",
        "natural_waist",
    ):
        assert f'"{control_code}"' in migration

    assert "op.bulk_insert(taxonomy_items" in migration
    assert "op.bulk_insert(wear_controls" in migration
    assert "delete().where(wear_controls.c.id.in_(" in migration
    assert "delete().where(taxonomy_items.c.code.in_(" in migration
