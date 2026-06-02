from __future__ import annotations

import pytest

from src.adapters.ai.image_editing_stub import StubImageEditingProvider
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.provider_generation import TryOnProviderGenerationAdapter
from src.domain.try_on import TryOnInputMetadata, TryOnStoredInput, TryOnUploadRole


@pytest.mark.asyncio
async def test_try_on_provider_generation_returns_generated_artifact_result() -> None:
    object_storage = InMemoryObjectStorage()
    adapter = TryOnProviderGenerationAdapter(
        image_editing_provider=StubImageEditingProvider(),
        object_storage=object_storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
    )

    result = await adapter.generate(
        job_id="try_on_job_1",
        input_metadata=[
            TryOnInputMetadata(
                role=TryOnUploadRole.HUMAN_PHOTO,
                filename="human.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnInputMetadata(
                role=TryOnUploadRole.GARMENT_PHOTO,
                filename="garment.jpg",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="in_memory",
                uri="memory://fitfabrica/tenants/public/try-on/try_on_job_1/human_photo/human.jpg",
                object_key="fitfabrica/tenants/public/try-on/try_on_job_1/human_photo/human.jpg",
                object_name="fitfabrica/tenants/public/try-on/try_on_job_1/human_photo/human.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnStoredInput(
                role=TryOnUploadRole.GARMENT_PHOTO,
                storage_backend="in_memory",
                uri="memory://fitfabrica/tenants/public/try-on/try_on_job_1/garment_photo/garment.jpg",
                object_key="fitfabrica/tenants/public/try-on/try_on_job_1/garment_photo/garment.jpg",
                object_name="fitfabrica/tenants/public/try-on/try_on_job_1/garment_photo/garment.jpg",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
    )

    assert result.result_image.kind == "generated_artifact"
    assert result.result_image.url.startswith("memory://fitfabrica/tenants/public/try-on/try_on_job_1/result_image/")
    assert result.quality_report.checks[0].name == "provider_runtime_dispatch"
    assert "provider-runtime" in result.stylist_note.lower()
