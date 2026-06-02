"""In-memory repository fallback for product-card workflows."""

from __future__ import annotations

from src.domain.product_card import ProductCardDraft, ProductCardJobRecord, ProductCardRequest, ProductCardVersionRecord


class InMemoryProductCardRepository:
    """Store product-card jobs and versions in memory when SQL is unavailable."""

    def __init__(self) -> None:
        """Initialize in-memory job and version stores."""
        self._jobs: dict[str, ProductCardJobRecord] = {}
        self._versions: dict[str, list[ProductCardVersionRecord]] = {}

    async def create_job(self, *, request: ProductCardRequest, asset_keys: list[str], now) -> ProductCardJobRecord:
        """Create one in-memory product-card job."""
        job = ProductCardJobRecord(
            job_id=f"product_card_{len(self._jobs) + 1}",
            status="accepted",
            target_channel=request.target_channel,
            brand_tone=request.brand_tone,
            title_hint=request.title_hint,
            asset_keys=list(asset_keys),
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        return job

    async def save_generated_version(self, *, job_id: str, draft: ProductCardDraft, now) -> ProductCardVersionRecord:
        """Persist one generated version in memory."""
        version = ProductCardVersionRecord(
            version_id=f"{job_id}_v{len(self._versions.get(job_id, [])) + 1}",
            job_id=job_id,
            title=draft.title,
            description=draft.description,
            bullet_points=list(draft.bullet_points),
            attributes=dict(draft.attributes),
            created_at=now,
        )
        self._versions.setdefault(job_id, []).append(version)
        return version

    async def get_latest_version(self, job_id: str) -> ProductCardVersionRecord | None:
        """Return the latest generated version for the requested in-memory job."""
        versions = self._versions.get(job_id, [])
        return versions[-1] if versions else None

    async def get_job(self, job_id: str) -> ProductCardJobRecord | None:
        """Return the requested in-memory product-card job."""
        return self._jobs.get(job_id)

    async def mark_completed(self, job_id: str, *, now) -> ProductCardJobRecord:
        """Mark the requested in-memory job as completed."""
        job = self._jobs[job_id]
        completed = job.model_copy(update={"status": "completed", "updated_at": now})
        self._jobs[job_id] = completed
        return completed
