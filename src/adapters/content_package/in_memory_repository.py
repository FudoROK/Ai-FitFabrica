"""In-memory repository fallback for content-package workflows."""

from __future__ import annotations

from src.domain.content_package import (
    ContentPackageJobRecord,
    ContentPackageOption,
    ContentPackageRequest,
    ContentPackageVersionRecord,
)


class InMemoryContentPackageRepository:
    """Store content-package jobs and versions in memory when SQL is unavailable."""

    def __init__(self) -> None:
        """Initialize in-memory stores for jobs and versions."""
        self._jobs: dict[str, ContentPackageJobRecord] = {}
        self._versions: dict[str, list[ContentPackageVersionRecord]] = {}

    async def create_job(self, *, request: ContentPackageRequest, now) -> ContentPackageJobRecord:
        """Create one in-memory content-package job."""
        job = ContentPackageJobRecord(
            job_id=f"content_package_{len(self._jobs) + 1}",
            product_card_version_id=request.product_card_version_id,
            package_name=request.package_name,
            status="accepted",
            requested_channels=list(request.requested_channels),
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        return job

    async def save_package_version(
        self,
        *,
        job_id: str,
        package_name: str,
        assets: list[ContentPackageOption],
        artifact_keys: list[str],
        now,
    ) -> ContentPackageVersionRecord:
        """Persist one generated content-package version in memory."""
        version = ContentPackageVersionRecord(
            version_id=f"{job_id}_v{len(self._versions.get(job_id, [])) + 1}",
            job_id=job_id,
            package_name=package_name,
            assets=list(assets),
            created_at=now,
        )
        self._versions.setdefault(job_id, []).append(version)
        return version

    async def get_latest_version(self, job_id: str) -> ContentPackageVersionRecord | None:
        """Return the latest generated version for the requested in-memory job."""
        versions = self._versions.get(job_id, [])
        return versions[-1] if versions else None

    async def get_job(self, job_id: str) -> ContentPackageJobRecord | None:
        """Return the requested in-memory content-package job."""
        return self._jobs.get(job_id)

    async def list_recent(self, *, limit: int) -> list[ContentPackageJobRecord]:
        """Return recent in-memory content-package jobs ordered by update time."""
        jobs = sorted(self._jobs.values(), key=lambda job: job.updated_at, reverse=True)
        return jobs[:limit]

    async def mark_completed(self, job_id: str, *, now) -> ContentPackageJobRecord:
        """Mark the requested in-memory content-package job as completed."""
        job = self._jobs[job_id]
        completed = job.model_copy(update={"status": "completed", "updated_at": now})
        self._jobs[job_id] = completed
        return completed
