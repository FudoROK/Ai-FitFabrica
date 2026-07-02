"""SQL-backed repositories for product-card workflow persistence."""

from __future__ import annotations

from sqlalchemy import select

from src.domain.product_card import (
    ProductCardDraft,
    ProductCardGarmentAnalysis,
    ProductCardJobRecord,
    ProductCardRequest,
    ProductCardVersionRecord,
)

from .product_card_models import ProductCardGarmentAnalysisRow, ProductCardJobRow, ProductCardSourceAssetRow, ProductCardVersionRow
from .product_card_serialization import job_record_from_rows, version_record_from_row


class SqlProductCardRepository:
    """Persist product-card jobs and generated versions in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def create_job(
        self,
        *,
        request: ProductCardRequest,
        asset_keys: list[str],
        now,
    ) -> ProductCardJobRecord:
        """Create a product-card job and its stored source-asset references."""
        job_id = f"product_card_{int(now.timestamp() * 1000000)}"
        job_row = ProductCardJobRow(
            job_id=job_id,
            status="accepted",
            category=request.category,
            target_channel=request.target_channel,
            brand_tone=request.brand_tone,
            title_hint=request.title_hint,
            created_at=now,
            updated_at=now,
        )
        asset_rows = [
            ProductCardSourceAssetRow(
                job_id=job_id,
                object_key=object_key,
                position=index,
                created_at=now,
            )
            for index, object_key in enumerate(asset_keys)
        ]
        async with self._session_factory() as session:
            session.add(job_row)
            session.add_all(asset_rows)
            await session.commit()
        return job_record_from_rows(job_row=job_row, asset_rows=asset_rows)

    async def save_generated_version(
        self,
        *,
        job_id: str,
        draft: ProductCardDraft,
        now,
    ) -> ProductCardVersionRecord:
        """Persist one generated product-card version for the requested job."""
        version_row = ProductCardVersionRow(
            version_id=f"{job_id}_v1",
            job_id=job_id,
            title=draft.title,
            description=draft.description,
            bullet_points_json=list(draft.bullet_points),
            attributes_json=dict(draft.attributes),
            created_at=now,
        )
        async with self._session_factory() as session:
            session.add(version_row)
            await session.commit()
        return version_record_from_row(version_row)

    async def save_garment_analysis(self, analysis: ProductCardGarmentAnalysis) -> ProductCardGarmentAnalysis:
        """Persist one validated reusable garment analysis."""
        row = ProductCardGarmentAnalysisRow(
            job_id=analysis.job_id,
            invocation_id=analysis.invocation_id,
            prompt_version=analysis.prompt_version,
            contract_version=analysis.contract_version,
            garment_type=analysis.garment_type,
            dominant_color=analysis.dominant_color,
            confidence=analysis.confidence,
            uncertainty_level=analysis.uncertainty_level,
            analysis_json=analysis.model_dump(mode="json"),
            completed_at=analysis.completed_at,
        )
        async with self._session_factory() as session:
            await session.merge(row)
            await session.commit()
        return analysis

    async def get_garment_analysis(self, job_id: str) -> ProductCardGarmentAnalysis | None:
        """Return the saved garment analysis for one Product Card job."""
        async with self._session_factory() as session:
            row = await session.get(ProductCardGarmentAnalysisRow, job_id)
            return None if row is None else ProductCardGarmentAnalysis.model_validate(row.analysis_json)

    async def get_latest_version(self, job_id: str) -> ProductCardVersionRecord | None:
        """Return the latest generated version for the requested job identifier."""
        async with self._session_factory() as session:
            row = (
                await session.scalars(
                    select(ProductCardVersionRow)
                    .where(ProductCardVersionRow.job_id == job_id)
                    .order_by(ProductCardVersionRow.created_at.desc())
                )
            ).first()
            return None if row is None else version_record_from_row(row)

    async def get_job(self, job_id: str) -> ProductCardJobRecord | None:
        """Return the persisted product-card job for the requested identifier."""
        async with self._session_factory() as session:
            job_row = await session.get(ProductCardJobRow, job_id)
            if job_row is None:
                return None
            asset_rows = (
                await session.scalars(
                    select(ProductCardSourceAssetRow)
                    .where(ProductCardSourceAssetRow.job_id == job_id)
                )
            ).all()
            return job_record_from_rows(job_row=job_row, asset_rows=list(asset_rows))

    async def list_recent(self, *, limit: int) -> list[ProductCardJobRecord]:
        """Return recent persisted product-card jobs for workspace history surfaces."""
        async with self._session_factory() as session:
            job_rows = (
                await session.scalars(
                    select(ProductCardJobRow)
                    .order_by(ProductCardJobRow.updated_at.desc())
                    .limit(limit)
                )
            ).all()
            jobs: list[ProductCardJobRecord] = []
            for job_row in job_rows:
                asset_rows = (
                    await session.scalars(
                        select(ProductCardSourceAssetRow)
                        .where(ProductCardSourceAssetRow.job_id == job_row.job_id)
                    )
                ).all()
                jobs.append(job_record_from_rows(job_row=job_row, asset_rows=list(asset_rows)))
            return jobs

    async def mark_completed(self, job_id: str, *, now) -> ProductCardJobRecord:
        """Mark the requested job as completed and return the updated job record."""
        async with self._session_factory() as session:
            job_row = await session.get(ProductCardJobRow, job_id)
            if job_row is None:
                raise LookupError(f"Unknown product-card job: {job_id}")
            job_row.status = "completed"
            job_row.updated_at = now
            asset_rows = (
                await session.scalars(
                    select(ProductCardSourceAssetRow)
                    .where(ProductCardSourceAssetRow.job_id == job_id)
                )
            ).all()
            await session.commit()
            return job_record_from_rows(job_row=job_row, asset_rows=list(asset_rows))

    async def mark_failed(self, job_id: str, *, now) -> ProductCardJobRecord:
        """Mark the requested job as failed and return the updated job record."""
        async with self._session_factory() as session:
            job_row = await session.get(ProductCardJobRow, job_id)
            if job_row is None:
                raise LookupError(f"Unknown product-card job: {job_id}")
            job_row.status = "failed"
            job_row.updated_at = now
            asset_rows = (
                await session.scalars(
                    select(ProductCardSourceAssetRow)
                    .where(ProductCardSourceAssetRow.job_id == job_id)
                )
            ).all()
            await session.commit()
            return job_record_from_rows(job_row=job_row, asset_rows=list(asset_rows))
