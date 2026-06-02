from __future__ import annotations

from types import SimpleNamespace

from src.adapters.ai.vertex_virtual_try_on_client import VertexVirtualTryOnClient


class _FakeModels:
    """SDK-like models surface for recontext_image tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def recontext_image(self, *, model: str, source: object, config: object | None = None) -> object:
        """Capture request and return a generated-image shaped response."""
        self.calls.append({"model": model, "source": source, "config": config})
        return SimpleNamespace(
            generated_images=[
                SimpleNamespace(
                    image=SimpleNamespace(image_bytes=b"generated-image", mime_type="image/png")
                )
            ]
        )


class _FakeSdkClient:
    """SDK-like client carrying the models sub-surface."""

    def __init__(self) -> None:
        self.models = _FakeModels()


def test_vertex_virtual_try_on_client_returns_generated_bytes() -> None:
    sdk_client = _FakeSdkClient()
    client = VertexVirtualTryOnClient(
        project="fitfabrica-test",
        location="global",
        model="virtual-try-on-001",
        client=sdk_client,
    )

    image_bytes, mime_type = client.generate(
        person_image_bytes=b"person",
        person_image_mime_type="image/jpeg",
        garment_image_bytes=b"garment",
        garment_image_mime_type="image/jpeg",
        prompt="Create a realistic virtual try-on image.",
    )

    assert image_bytes == b"generated-image"
    assert mime_type == "image/png"
    assert sdk_client.models.calls[0]["model"] == "virtual-try-on-001"
