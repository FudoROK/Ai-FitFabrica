from __future__ import annotations

import pytest

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.vertex_virtual_try_on_generation import VertexVirtualTryOnGenerationAdapter
from src.domain.try_on import TryOnInputMetadata, TryOnStoredInput, TryOnUploadRole
from src.domain.try_on_instruction import TryOnGenerationInstruction


class _FakeVertexVirtualTryOnClient:
    """Deterministic fake client for Vertex Virtual Try-On adapter tests."""

    provider_name = "vertex_virtual_try_on"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate(
        self,
        *,
        person_image_bytes: bytes,
        person_image_mime_type: str,
        garment_image_bytes: bytes,
        garment_image_mime_type: str,
        prompt: str,
    ) -> tuple[bytes, str]:
        """Capture the request and return deterministic image bytes."""
        self.calls.append(
            {
                "person_image_bytes": person_image_bytes,
                "person_image_mime_type": person_image_mime_type,
                "garment_image_bytes": garment_image_bytes,
                "garment_image_mime_type": garment_image_mime_type,
                "prompt": prompt,
            }
        )
        return (b"vertex-image-bytes", "image/png")


@pytest.mark.asyncio
async def test_vertex_virtual_try_on_generation_persists_real_provider_bytes() -> None:
    object_storage = InMemoryObjectStorage()
    human_key = "fitfabrica/tenants/public/try-on/try_on_job_1/human_photo/human.jpg"
    garment_key = "fitfabrica/tenants/public/try-on/try_on_job_1/garment_photo/garment.jpg"
    object_storage.put_bytes(object_key=human_key, payload=b"human-bytes", content_type="image/jpeg")
    object_storage.put_bytes(object_key=garment_key, payload=b"garment-bytes", content_type="image/jpeg")
    fake_client = _FakeVertexVirtualTryOnClient()
    adapter = VertexVirtualTryOnGenerationAdapter(
        object_storage=object_storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
        vertex_client=fake_client,
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
                uri=f"memory://{human_key}",
                object_key=human_key,
                object_name=human_key,
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnStoredInput(
                role=TryOnUploadRole.GARMENT_PHOTO,
                storage_backend="in_memory",
                uri=f"memory://{garment_key}",
                object_key=garment_key,
                object_name=garment_key,
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

    assert fake_client.calls[0]["person_image_bytes"] == b"human-bytes"
    assert fake_client.calls[0]["garment_image_bytes"] == b"garment-bytes"
    assert result.result_image.kind == "generated_artifact"
    assert result.result_image.url.endswith("/result_image/result.png")
    assert object_storage.get_bytes("fitfabrica/tenants/public/try-on/try_on_job_1/result_image/result.png") == b"vertex-image-bytes"

