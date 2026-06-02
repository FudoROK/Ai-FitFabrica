from __future__ import annotations

from src.adapters.ai.image_editing_stub import StubImageEditingProvider
from src.adapters.ai.image_generation_stub import StubImageGenerationProvider
from src.domain.provider_models import ImageEditingRequest, ImageGenerationRequest


def test_image_stub_provider_returns_backend_owned_placeholder_result() -> None:
    generation_provider = StubImageGenerationProvider()
    editing_provider = StubImageEditingProvider()

    generation_result = generation_provider.generate(
        ImageGenerationRequest(
            task="product_card_generation",
            prompt="Create a premium fashion image",
            output_mime_type="image/png",
        )
    )
    editing_result = editing_provider.edit(
        ImageEditingRequest(
            task="repair_try_on_result",
            prompt="Fix sleeve artifact",
            source_object_key="tenant/jobs/source.png",
            reference_object_keys=["tenant/jobs/garment.png"],
            output_mime_type="image/png",
        )
    )

    assert generation_result.provider == "stub_image_generation"
    assert generation_result.output_object_key.endswith(".png")
    assert editing_result.provider == "stub_image_editing"
    assert editing_result.output_object_key.endswith(".png")
