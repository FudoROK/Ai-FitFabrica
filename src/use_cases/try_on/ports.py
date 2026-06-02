"""Ports for Try-On workflow persistence and generation."""
from __future__ import annotations

from typing import Protocol

from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnResult,
    TryOnStoredInput,
    TryOnUploadRole,
)


class TryOnJobRepositoryPort(Protocol):
    """Persistence boundary for Try-On job aggregates."""

    async def save(self, job: TryOnJob) -> None:
        """Persist the latest state of a Try-On job."""
        ...

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a Try-On job by identifier, if it exists."""
        ...


class TryOnFileStoragePort(Protocol):
    """Port for persisting validated Try-On upload bytes."""

    async def save_upload(
        self,
        *,
        job_id: str,
        role: TryOnUploadRole,
        filename: str,
        content_type: str,
        payload: bytes,
        sha256_hex: str,
    ) -> TryOnStoredInput:
        """Persist upload bytes and return a backend-owned storage reference."""
        ...


class TryOnGenerationPort(Protocol):
    """Generation boundary used by the workflow service."""

    generation_mode: TryOnGenerationMode

    async def generate(
        self,
        *,
        job_id: str,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
    ) -> TryOnResult:
        """Generate a Try-On result for validated input metadata."""
        ...


class TryOnQualityVerifierPort(Protocol):
    """Quality-verification boundary used after Try-On generation."""

    async def verify(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ):
        """Verify the generated Try-On result and return a backend-owned quality report."""
        ...


class TryOnRepairPort(Protocol):
    """Repair boundary used when quality verification recommends a local fix."""

    async def repair(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
        quality_report,
    ) -> TryOnResult:
        """Repair the generated Try-On result and return an updated result artifact."""
        ...


class TryOnStylistPort(Protocol):
    """Stylist boundary used to generate the final user-facing Try-On explanation."""

    async def generate_note(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> str:
        """Return the final stylist note for a completed Try-On result."""
        ...
