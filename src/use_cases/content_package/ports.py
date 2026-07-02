"""Workflow-facing ports for content-package orchestration."""

from __future__ import annotations

from typing import Protocol

from src.domain.content_package import (
    ContentPackageJobRecord,
    ContentPackageOption,
    ContentPackageRequest,
    ContentPackageVersionRecord,
)


class ContentPackageRepositoryPort(Protocol):
    """Port for durable content-package workflow persistence."""

    async def create_job(self, *, request: ContentPackageRequest, now) -> ContentPackageJobRecord:
        """Create one durable content-package job."""

    async def save_package_version(
        self,
        *,
        job_id: str,
        package_name: str,
        assets: list[ContentPackageOption],
        artifact_keys: list[str],
        now,
    ) -> ContentPackageVersionRecord:
        """Persist one generated content-package version."""

    async def mark_completed(self, job_id: str, *, now) -> ContentPackageJobRecord:
        """Mark the requested job as completed."""

    async def get_job(self, job_id: str) -> ContentPackageJobRecord | None:
        """Return the persisted job for the requested identifier."""

    async def get_latest_version(self, job_id: str) -> ContentPackageVersionRecord | None:
        """Return the latest generated version for the requested job."""

    async def list_recent(self, *, limit: int) -> list[ContentPackageJobRecord]:
        """Return recent content-package jobs for workspace history surfaces."""


class ContentPackageArtifactStoragePort(Protocol):
    """Port for persisting generated content-package artifacts."""

    async def store_generated_assets(
        self,
        *,
        job_id: str,
        assets: list[ContentPackageOption],
    ) -> list[str]:
        """Persist generated package artifacts and return their object keys."""


class ContentPackageGenerationPort(Protocol):
    """Port for provider-neutral content-package generation."""

    async def generate(self, *, request: ContentPackageRequest) -> list[ContentPackageOption]:
        """Generate a structured content-package asset list."""
