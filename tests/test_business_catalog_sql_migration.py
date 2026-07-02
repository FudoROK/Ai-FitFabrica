from pathlib import Path

from src.adapters.database.sql.business_catalog_models import (
    BusinessCatalogImportJobRow,
    BusinessCatalogImportRowErrorRow,
    BusinessMerchantRow,
    BusinessProductImageRow,
    BusinessProductOfferRow,
    BusinessProductRow,
)


def test_business_catalog_sql_models_have_a_head_migration() -> None:
    migration = Path("alembic/versions/20260628_000021_business_catalog.py").read_text(encoding="utf-8")

    assert 'down_revision = "20260624_000020"' in migration
    for model in (
        BusinessMerchantRow,
        BusinessProductRow,
        BusinessProductImageRow,
        BusinessProductOfferRow,
        BusinessCatalogImportJobRow,
        BusinessCatalogImportRowErrorRow,
    ):
        assert f'"{model.__tablename__}"' in migration


def test_business_catalog_search_index_status_migration_exists() -> None:
    migration = Path("alembic/versions/20260630_000022_business_catalog_search_index_status.py").read_text(
        encoding="utf-8"
    )

    assert 'down_revision = "20260628_000021"' in migration
    assert '"search_index_status"' in migration
    assert '"search_index_error"' in migration
    assert '"search_indexed_at"' in migration
    assert "ix_business_products_search_index_status" in migration


def test_business_catalog_category_validation_migration_exists() -> None:
    migration = Path("alembic/versions/20260701_000024_business_catalog_category_validation.py").read_text(
        encoding="utf-8"
    )

    assert 'down_revision = "20260701_000023"' in migration
    assert '"category_validation_status"' in migration
    assert '"category_validation_reason"' in migration
    assert '"visual_category"' in migration
    assert '"visual_category_confidence"' in migration
    assert '"category_validated_at"' in migration
    assert "ix_business_products_category_validation_status" in migration


def test_marketplace_discovery_candidate_migration_exists() -> None:
    migration = Path("alembic/versions/20260702_000025_marketplace_discovery_candidates.py").read_text(
        encoding="utf-8"
    )

    assert 'down_revision = "20260701_000024"' in migration
    assert '"marketplace_discovery_candidates"' in migration
    assert '"candidate_id"' in migration
    assert '"workspace_id"' in migration
    assert '"business_id"' in migration
    assert '"source_url"' in migration
    assert '"image_url"' in migration
    assert '"media_url"' in migration
    assert '"brand"' in migration
    assert '"price_amount"' in migration
    assert '"currency"' in migration
    assert '"raw_payload_json"' in migration
    assert '"metadata_json"' in migration
    assert '"status"' in migration
    assert '"rejection_reason"' in migration
    assert '"approved_at"' in migration
    assert '"rejected_at"' in migration
    assert '"created_at"' in migration
    assert '"updated_at"' in migration
    assert "uq_marketplace_discovery_candidates_scope_source_url" in migration
    assert "ix_marketplace_discovery_candidates_status_source" in migration
