from __future__ import annotations

from types import SimpleNamespace

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.domain.provider_models import ImageEditingRequest


class _FakeModels:
    """Capture image-edit calls while returning generated image bytes."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.generate_content_calls: list[dict[str, object]] = []

    def edit_image(self, *, model: str, prompt: str, reference_images: list[object], config: object) -> object:
        """Return a minimal SDK-shaped image-edit response."""
        self.calls.append(
            {
                "model": model,
                "prompt": prompt,
                "reference_images": reference_images,
                "config": config,
            }
        )
        return SimpleNamespace(
            generated_images=[
                SimpleNamespace(
                    image=SimpleNamespace(
                        image_bytes=b"edited-image-bytes",
                        mime_type="image/webp",
                    )
                )
            ]
        )

    def generate_content(self, *, model: str, contents: list[object]) -> object:
        """Return a minimal Gemini native image response."""
        self.generate_content_calls.append({"model": model, "contents": contents})
        return SimpleNamespace(
            candidates=[
                SimpleNamespace(
                    content=SimpleNamespace(
                        parts=[
                            SimpleNamespace(text="edited"),
                            SimpleNamespace(
                                inline_data=SimpleNamespace(
                                    data=b"gemini-edited-image-bytes",
                                    mime_type="image/png",
                                )
                            ),
                        ]
                    )
                )
            ]
        )


class _FakeClient:
    """Expose the GenAI models surface used by the adapter."""

    def __init__(self) -> None:
        self.models = _FakeModels()


def test_google_genai_image_editing_provider_persists_real_edited_bytes() -> None:
    from src.adapters.ai.google_genai_image_editing import GoogleGenAIImageEditingProvider

    storage = InMemoryObjectStorage()
    storage.put_bytes(object_key="source/result.webp", payload=b"source-bytes", content_type="image/webp")
    storage.put_bytes(object_key="refs/human.jpg", payload=b"human-bytes", content_type="image/jpeg")
    storage.put_bytes(object_key="refs/garment.png", payload=b"garment-bytes", content_type="image/png")
    client = _FakeClient()

    provider = GoogleGenAIImageEditingProvider(
        project="project-id",
        location="us-central1",
        model="imagen-edit-test",
        object_storage=storage,
        root_prefix="fitfabrica-test",
        client=client,
    )

    result = provider.edit(
        ImageEditingRequest(
            task="repair_try_on_result",
            prompt="Fix only local background artifacts.",
            source_object_key="source/result.webp",
            reference_object_keys=["refs/human.jpg", "refs/garment.png"],
            output_mime_type="image/webp",
        )
    )

    assert result.provider == "google_genai_image_editing"
    assert result.output_mime_type == "image/webp"
    assert result.output_object_key.startswith("fitfabrica-test/provider-artifacts/image-editing/repair_try_on_result/")
    assert storage.get_bytes(result.output_object_key) == b"edited-image-bytes"
    assert client.models.calls[0]["model"] == "imagen-edit-test"
    assert client.models.calls[0]["prompt"] == "Fix only local background artifacts."
    assert len(client.models.calls[0]["reference_images"]) == 3


def test_google_genai_image_editing_provider_supports_gemini_native_image_models() -> None:
    from src.adapters.ai.google_genai_image_editing import GoogleGenAIImageEditingProvider

    storage = InMemoryObjectStorage()
    storage.put_bytes(object_key="source/result.webp", payload=b"source-bytes", content_type="image/webp")
    storage.put_bytes(object_key="refs/human.jpg", payload=b"human-bytes", content_type="image/jpeg")
    storage.put_bytes(object_key="refs/garment.png", payload=b"garment-bytes", content_type="image/png")
    client = _FakeClient()

    provider = GoogleGenAIImageEditingProvider(
        project="project-id",
        location="us-central1",
        model="gemini-2.5-flash-image",
        object_storage=storage,
        root_prefix="fitfabrica-test",
        client=client,
    )

    result = provider.edit(
        ImageEditingRequest(
            task="repair_try_on_result",
            prompt="Fix only the malformed hand while preserving the face and garment.",
            source_object_key="source/result.webp",
            reference_object_keys=["refs/human.jpg", "refs/garment.png"],
            output_mime_type="image/png",
        )
    )

    assert result.provider == "google_genai_image_editing"
    assert result.output_mime_type == "image/png"
    assert storage.get_bytes(result.output_object_key) == b"gemini-edited-image-bytes"
    assert client.models.generate_content_calls[0]["model"] == "gemini-2.5-flash-image"
    assert client.models.calls == []
    assert len(client.models.generate_content_calls[0]["contents"]) == 4
