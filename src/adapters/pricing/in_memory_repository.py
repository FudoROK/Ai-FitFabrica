"""In-memory repository fallback for pricing workflows."""

from __future__ import annotations

from src.domain.pricing import PricingJobRecord, PricingRecommendation, PricingRecommendationRecord, PricingRequest


class InMemoryPricingRepository:
    """Store pricing jobs and recommendations in memory when SQL is unavailable."""

    def __init__(self) -> None:
        """Initialize in-memory stores for jobs and recommendations."""
        self._jobs: dict[str, PricingJobRecord] = {}
        self._recommendations: dict[str, list[PricingRecommendationRecord]] = {}

    async def create_job(self, *, request: PricingRequest, now) -> PricingJobRecord:
        """Create one in-memory pricing job."""
        job = PricingJobRecord(
            job_id=f"pricing_{len(self._jobs) + 1}",
            product_id=request.product_id,
            target_currency=request.target_currency,
            desired_margin_percent=request.desired_margin_percent,
            status="accepted",
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        return job

    async def save_recommendation(
        self,
        *,
        job_id: str,
        recommendation: PricingRecommendation,
        now,
    ) -> PricingRecommendationRecord:
        """Persist one generated pricing recommendation in memory."""
        record = PricingRecommendationRecord(
            recommendation_id=f"{job_id}_v{len(self._recommendations.get(job_id, [])) + 1}",
            job_id=job_id,
            recommendation=recommendation,
            created_at=now,
        )
        self._recommendations.setdefault(job_id, []).append(record)
        return record

    async def get_job(self, job_id: str) -> PricingJobRecord | None:
        """Return the requested in-memory pricing job."""
        return self._jobs.get(job_id)

    async def get_latest_recommendation(self, job_id: str) -> PricingRecommendationRecord | None:
        """Return the latest generated in-memory recommendation for the requested job."""
        values = self._recommendations.get(job_id, [])
        return values[-1] if values else None

    async def mark_completed(self, job_id: str, *, now) -> PricingJobRecord:
        """Mark the requested in-memory pricing job as completed."""
        job = self._jobs[job_id]
        completed = job.model_copy(update={"status": "completed", "updated_at": now})
        self._jobs[job_id] = completed
        return completed
