"""Vertex AI Virtual Try-On client wrapper."""

from __future__ import annotations

import importlib
import importlib.util

_GENAI_SPEC = importlib.util.find_spec("google.genai")
genai = importlib.import_module("google.genai") if _GENAI_SPEC is not None else None
types = importlib.import_module("google.genai.types") if _GENAI_SPEC is not None else None


class VertexVirtualTryOnClient:
    """Small wrapper around the Google GenAI Vertex Virtual Try-On API."""

    provider_name = "vertex_virtual_try_on"

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
        client: object | None = None,
    ) -> None:
        """Store Vertex runtime configuration and optional injected SDK client."""
        self._project = project
        self._location = location
        self._model = model
        self._client = client

    def generate(
        self,
        *,
        person_image_bytes: bytes,
        person_image_mime_type: str,
        garment_image_bytes: bytes,
        garment_image_mime_type: str,
        prompt: str,
    ) -> tuple[bytes, str]:
        """Generate a real Try-On image through the Vertex Virtual Try-On model."""
        sdk_types = self._require_sdk_types()
        response = self._require_client().models.recontext_image(
            model=self._model,
            source=sdk_types.RecontextImageSource(
                prompt=prompt,
                person_image=sdk_types.Image(
                    image_bytes=person_image_bytes,
                    mime_type=person_image_mime_type,
                ),
                product_images=[
                    sdk_types.ProductImage(
                        product_image=sdk_types.Image(
                            image_bytes=garment_image_bytes,
                            mime_type=garment_image_mime_type,
                        )
                    )
                ],
            ),
        )
        generated_images = getattr(response, "generated_images", None)
        if not isinstance(generated_images, list) or not generated_images:
            raise RuntimeError("vertex_virtual_try_on_returned_no_generated_images")
        first_image = getattr(generated_images[0], "image", None)
        image_bytes = getattr(first_image, "image_bytes", None) if first_image is not None else None
        mime_type = getattr(first_image, "mime_type", None) if first_image is not None else None
        if not isinstance(image_bytes, bytes) or not image_bytes:
            raise RuntimeError("vertex_virtual_try_on_returned_no_image_bytes")
        if not isinstance(mime_type, str) or not mime_type:
            raise RuntimeError("vertex_virtual_try_on_returned_no_mime_type")
        return image_bytes, mime_type

    def _require_client(self) -> object:
        """Return the cached SDK client or lazily build one."""
        if self._client is None:
            if genai is None:
                raise RuntimeError("google-genai SDK is not installed")
            self._client = genai.Client(
                vertexai=True,
                project=self._project,
                location=self._location,
            )
        return self._client

    @staticmethod
    def _require_sdk_types():
        """Return the GenAI SDK types module required for typed request payloads."""
        if types is None:
            raise RuntimeError("google-genai SDK types are not installed")
        return types
