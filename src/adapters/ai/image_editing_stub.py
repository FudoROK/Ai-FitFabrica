"""Stub image editing adapter for backend wiring tests."""

from __future__ import annotations

from hashlib import sha256

from src.domain.provider_models import ImageEditingRequest, ImageEditingResult


class StubImageEditingProvider:
    """Return deterministic artifact references for edited images."""

    provider_name = "stub_image_editing"

    def edit(self, request: ImageEditingRequest) -> ImageEditingResult:
        """Build a placeholder edited object key from source and prompt."""
        suffix = request.output_mime_type.split("/")[-1]
        references = ",".join(sorted(request.reference_object_keys))
        digest = sha256(f"{request.source_object_key}:{references}:{request.prompt}".encode("utf-8")).hexdigest()[:16]
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=f"edited/{request.task}/{digest}.{suffix}",
            output_mime_type=request.output_mime_type,
            provider=self.provider_name,
        )
