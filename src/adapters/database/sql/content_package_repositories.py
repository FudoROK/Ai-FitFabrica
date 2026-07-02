"""SQL-backed repositories for content-package workflow persistence."""

from __future__ import annotations

from sqlalchemy import select

from src.domain.content_package import (
    ContentPackageJobRecord,
    ContentPackageOption,
    ContentPackageRequest,
    ContentPackageVersionRecord,
)

from .content_package_models import ContentPackageArtifactRow, ContentPackageJobRow, ContentPackageVersionRow
from .content_package_serialization import job_record_from_row, version_record_from_rows


class SqlContentPackageRepository:
    """Persist content-package jobs and versions in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def create_job(
        self,
        *,
        request: ContentPackageRequest,
        now,
    ) -> ContentPackageJobRecord:
        """Create one durable content-package job."""
        job_row = ContentPackageJobRow(
            job_id=f"content_package_{int(now.timestamp() * 1000000)}",
            product_card_version_id=request.product_card_version_id,
            package_name=request.package_name,
            requested_channels_csv=",".join(request.requested_channels),
            status="accepted",
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            session.add(job_row)
            await session.commit()
        return job_record_from_row(job_row)

    async def save_package_version(
        self,
        *,
        job_id: str,
        package_name: str,
        assets: list[ContentPackageOption],
        artifact_keys: list[str],
        now,
    ) -> ContentPackageVersionRecord:
        """Persist one generated content-package version and its artifact references."""
        version_id = f"{job_id}_v1"
        version_row = ContentPackageVersionRow(
            version_id=version_id,
            job_id=job_id,
            package_name=package_name,
            created_at=now,
        )
        artifact_rows = [
            ContentPackageArtifactRow(
                version_id=version_id,
                asset_kind=asset.asset_kind,
                label=asset.label,
                object_key=object_key,
                created_at=now,
            )
            for asset, object_key in zip(assets, artifact_keys, strict=True)
        ]
        async with self._session_factory() as session:
            session.add(version_row)
            session.add_all(artifact_rows)
            await session.commit()
        return version_record_from_rows(version_row=version_row, artifact_rows=artifact_rows)

    async def get_latest_version(self, job_id: str) -> ContentPackageVersionRecord | None:
        """Return the latest generated content-package version for the requested job."""
        async with self._session_factory() as session:
            version_row = (
                await session.scalars(
                    select(ContentPackageVersionRow)
                    .where(ContentPackageVersionRow.job_id == job_id)
                    .order_by(ContentPackageVersionRow.created_at.desc())
                )
            ).first()
            if version_row is None:
                return None
            artifact_rows = (
                await session.scalars(
                    select(ContentPackageArtifactRow)
                    .where(ContentPackageArtifactRow.version_id == version_row.version_id)
                )
            ).all()
            return version_record_from_rows(version_row=version_row, artifact_rows=list(artifact_rows))

    async def get_job(self, job_id: str) -> ContentPackageJobRecord | None:
        """Return the persisted content-package job for the requested identifier."""
        async with self._session_factory() as session:
            row = await session.get(ContentPackageJobRow, job_id)
            return None if row is None else job_record_from_row(row)

    async def list_recent(self, *, limit: int) -> list[ContentPackageJobRecord]:
        """Return recent persisted content-package jobs for workspace history surfaces."""
        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(ContentPackageJobRow)
                    .order_by(ContentPackageJobRow.updated_at.desc())
                    .limit(limit)
                )
            ).all()
            return [job_record_from_row(row) for row in rows]

    async def mark_completed(self, job_id: str, *, now) -> ContentPackageJobRecord:
        """Mark the requested content-package job as completed."""
        async with self._session_factory() as session:
            job_row = await session.get(ContentPackageJobRow, job_id)
            if job_row is None:
                raise LookupError(f"Unknown content-package job: {job_id}")
            job_row.status = "completed"
            job_row.updated_at = now
            await session.commit()
            return job_record_from_row(job_row)
