"""Stub image generation adapter for backend wiring tests."""

from __future__ import annotations

from hashlib import sha256

from src.domain.provider_models import ImageGenerationRequest, ImageGenerationResult


class StubImageGenerationProvider:
    """Return deterministic artifact references for generated images."""

    provider_name = "stub_image_generation"

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Build a placeholder object key from the task and prompt."""
        suffix = request.output_mime_type.split("/")[-1]
        digest = sha256(f"{request.task}:{request.prompt}".encode("utf-8")).hexdigest()[:16]
        return ImageGenerationResult(
            task=request.task,
            output_object_key=f"generated/{request.task}/{digest}.{suffix}",
            output_mime_type=request.output_mime_type,
            provider=self.provider_name,
        )
