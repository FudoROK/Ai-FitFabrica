from __future__ import annotations

import pytest

from src.adapters.ai.image_editing_stub import StubImageEditingProvider
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.provider_generation import TryOnProviderGenerationAdapter
from src.domain.provider_models import ImageEditingResult
from src.domain.try_on import TryOnInputMetadata, TryOnStoredInput, TryOnUploadRole
from src.domain.try_on_instruction import TryOnGenerationInstruction


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
        instruction=TryOnGenerationInstruction(
            invocation_id="instruction-1",
            prompt_version="try_on.v1",
            contract_version="try_on.contract.v1",
            instruction_summary="Preserve the approved person and garment.",
            confidence=0.9,
            uncertainty_level="low",
        ),
    )

    assert result.result_image.kind == "generated_artifact"
    assert result.result_image.url.startswith("memory://fitfabrica/tenants/public/try-on/try_on_job_1/result_image/")
    assert result.quality_report.checks[0].name == "provider_runtime_dispatch"
    assert "provider-runtime" in result.stylist_note.lower()


class _PersistingImageEditingProvider:
    provider_name = "persisting_image_editing"

    def __init__(self, *, storage: InMemoryObjectStorage) -> None:
        self._storage = storage

    def edit(self, request):
        output_key = "provider-artifacts/image-editing/try_on_generation/edited.webp"
        self._storage.put_bytes(
            object_key=output_key,
            payload=b"real-generated-image-bytes",
            content_type=request.output_mime_type,
        )
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=output_key,
            output_mime_type=request.output_mime_type,
            provider=self.provider_name,
        )


@pytest.mark.asyncio
async def test_try_on_provider_generation_persists_provider_edited_bytes() -> None:
    object_storage = InMemoryObjectStorage()
    adapter = TryOnProviderGenerationAdapter(
        image_editing_provider=_PersistingImageEditingProvider(storage=object_storage),
        object_storage=object_storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
    )

    result = await adapter.generate(
        job_id="try_on_job_1",
        input_metadata=[],
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="in_memory",
                uri="memory://human.jpg",
                object_key="human.jpg",
                object_name="human.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnStoredInput(
                role=TryOnUploadRole.GARMENT_PHOTO,
                storage_backend="in_memory",
                uri="memory://garment.jpg",
                object_key="garment.jpg",
                object_name="garment.jpg",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
        instruction=TryOnGenerationInstruction(
            invocation_id="instruction-1",
            prompt_version="try_on.v1",
            contract_version="try_on.contract.v1",
            instruction_summary="Preserve the approved person and garment.",
            confidence=0.9,
            uncertainty_level="low",
        ),
    )

    assert result.result_image._artifact_object_key is not None
    assert object_storage.get_bytes(result.result_image._artifact_object_key) == b"real-generated-image-bytes"
