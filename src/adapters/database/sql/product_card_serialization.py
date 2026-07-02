"""Mapping helpers between product-card SQL rows and domain records."""

from __future__ import annotations

from src.domain.product_card import ProductCardJobRecord, ProductCardVersionRecord

from .product_card_models import ProductCardJobRow, ProductCardSourceAssetRow, ProductCardVersionRow


def job_record_from_rows(
    *,
    job_row: ProductCardJobRow,
    asset_rows: list[ProductCardSourceAssetRow],
) -> ProductCardJobRecord:
    """Convert SQL job and asset rows into a domain job record."""
    ordered_assets = sorted(asset_rows, key=lambda row: row.position)
    return ProductCardJobRecord(
        job_id=job_row.job_id,
        status=job_row.status,
        category=job_row.category,
        target_channel=job_row.target_channel,
        brand_tone=job_row.brand_tone,
        title_hint=job_row.title_hint,
        asset_keys=[row.object_key for row in ordered_assets],
        created_at=job_row.created_at,
        updated_at=job_row.updated_at,
    )


def version_record_from_row(row: ProductCardVersionRow) -> ProductCardVersionRecord:
    """Convert a SQL product-card version row into a domain version record."""
    return ProductCardVersionRecord(
        version_id=row.version_id,
        job_id=row.job_id,
        title=row.title,
        description=row.description,
        bullet_points=list(row.bullet_points_json),
        attributes=dict(row.attributes_json),
        created_at=row.created_at,
    )
