"""Deterministic fallback stylist for Try-On explanations."""

from __future__ import annotations

from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnResult,
    TryOnStoredInput,
    TryOnUploadRole,
)
from src.use_cases.try_on.ports import TryOnStylistPort


class DeterministicTryOnStylist(TryOnStylistPort):
    """Build a safe, backend-owned stylist summary from workflow facts only."""

    async def generate_note(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> str:
        """Return a deterministic stylist note for the completed Try-On result."""
        roles = {item.role for item in input_metadata}
        has_human = TryOnUploadRole.HUMAN_PHOTO in roles
        has_garment = TryOnUploadRole.GARMENT_PHOTO in roles
        storage_backend = stored_inputs[0].storage_backend if stored_inputs else "unknown"
        return (
            "Try-On result is ready for review. "
            f"Generation mode: {generation_mode.value}. "
            f"Human input: {'yes' if has_human else 'no'}. "
            f"Garment input: {'yes' if has_garment else 'no'}. "
            f"Artifact backend: {storage_backend}. "
            "Use this image as a fit preview, then validate final buying decisions against the real product card."
        )
