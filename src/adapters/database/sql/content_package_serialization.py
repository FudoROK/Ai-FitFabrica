"""Mapping helpers between content-package SQL rows and domain records."""

from __future__ import annotations

from src.domain.content_package import (
    ContentPackageJobRecord,
    ContentPackageOption,
    ContentPackageVersionRecord,
)

from .content_package_models import ContentPackageArtifactRow, ContentPackageJobRow, ContentPackageVersionRow


def _split_channels(value: str) -> list[str]:
    return [item for item in value.split(",") if item]


def job_record_from_row(row: ContentPackageJobRow) -> ContentPackageJobRecord:
    """Convert a SQL content-package job row into a domain job record."""
    return ContentPackageJobRecord(
        job_id=row.job_id,
        product_card_version_id=row.product_card_version_id,
        package_name=row.package_name,
        status=row.status,
        requested_channels=_split_channels(row.requested_channels_csv),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def version_record_from_rows(
    *,
    version_row: ContentPackageVersionRow,
    artifact_rows: list[ContentPackageArtifactRow],
) -> ContentPackageVersionRecord:
    """Convert a SQL version row and artifact rows into a domain version record."""
    ordered_artifacts = sorted(artifact_rows, key=lambda row: row.id)
    return ContentPackageVersionRecord(
        version_id=version_row.version_id,
        job_id=version_row.job_id,
        package_name=version_row.package_name,
        assets=[
            ContentPackageOption(asset_kind=row.asset_kind, label=row.label)
            for row in ordered_artifacts
        ],
        created_at=version_row.created_at,
    )
