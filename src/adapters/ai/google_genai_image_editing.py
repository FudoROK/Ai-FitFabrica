"""Google GenAI image-editing adapter behind the backend-owned provider port."""

from __future__ import annotations

import importlib
import importlib.util
import mimetypes
from uuid import uuid4

from src.adapters.storage.contracts import ObjectStorage
from src.adapters.storage.object_naming import normalize_storage_filename
from src.domain.provider_models import ImageEditingRequest, ImageEditingResult


class GoogleGenAIImageEditingProvider:
    """Edit images through Google GenAI while keeping workflow code provider-neutral."""

    provider_name = "google_genai_image_editing"

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
        object_storage: ObjectStorage,
        root_prefix: str,
        client: object | None = None,
    ) -> None:
        """Store explicit Google runtime config and storage dependency."""
        self._project = project
        self._location = location
        self._model = model
        self._object_storage = object_storage
        self._root_prefix = root_prefix.strip("/") or "fitfabrica"
        self._client = client

    def edit(self, request: ImageEditingRequest) -> ImageEditingResult:
        """Run image editing, persist real edited bytes, and return an artifact reference."""
        if self._uses_gemini_native_image_model():
            return self._edit_with_gemini_native_image_model(request)
        return self._edit_with_imagen_edit_image(request)

    def _edit_with_imagen_edit_image(self, request: ImageEditingRequest) -> ImageEditingResult:
        """Run legacy Imagen edit-image API for models that still expose that surface."""
        sdk_types = self._require_sdk_types()
        reference_images = [
            self._build_raw_reference_image(
                sdk_types=sdk_types,
                object_key=request.source_object_key,
                reference_id=0,
                fallback_mime_type=request.output_mime_type,
            )
        ]
        reference_images.extend(
            self._build_raw_reference_image(
                sdk_types=sdk_types,
                object_key=object_key,
                reference_id=index,
                fallback_mime_type=request.output_mime_type,
            )
            for index, object_key in enumerate(request.reference_object_keys, start=1)
        )

        response = self._require_client().models.edit_image(
            model=self._model,
            prompt=request.prompt,
            reference_images=reference_images,
            config=sdk_types.EditImageConfig(
                number_of_images=1,
                output_mime_type=request.output_mime_type,
            ),
        )
        image_bytes, mime_type = self._extract_first_image(response)
        output_object_key = self._build_output_object_key(task=request.task, mime_type=mime_type)
        stored = self._object_storage.put_bytes(
            object_key=output_object_key,
            payload=image_bytes,
            content_type=mime_type,
        )
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=stored.object_key,
            output_mime_type=stored.content_type,
            provider=self.provider_name,
        )

    def _edit_with_gemini_native_image_model(self, request: ImageEditingRequest) -> ImageEditingResult:
        """Run Gemini native image editing through generate_content with image references."""
        sdk_types = self._require_sdk_types()
        contents: list[object] = [request.prompt]
        contents.append(self._build_content_image_part(sdk_types=sdk_types, object_key=request.source_object_key))
        contents.extend(
            self._build_content_image_part(sdk_types=sdk_types, object_key=object_key)
            for object_key in request.reference_object_keys
        )
        response = self._require_client().models.generate_content(model=self._model, contents=contents)
        image_bytes, mime_type = self._extract_first_inline_image(response, fallback_mime_type=request.output_mime_type)
        output_object_key = self._build_output_object_key(task=request.task, mime_type=mime_type)
        stored = self._object_storage.put_bytes(
            object_key=output_object_key,
            payload=image_bytes,
            content_type=mime_type,
        )
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=stored.object_key,
            output_mime_type=stored.content_type,
            provider=self.provider_name,
        )

    def _build_raw_reference_image(
        self,
        *,
        sdk_types,
        object_key: str,
        reference_id: int,
        fallback_mime_type: str,
    ) -> object:
        """Read one object-storage artifact and wrap it as a GenAI raw reference image."""
        payload = self._object_storage.get_bytes(object_key)
        mime_type = self._guess_mime_type(object_key=object_key, fallback=fallback_mime_type)
        return sdk_types.RawReferenceImage(
            reference_image=sdk_types.Image(image_bytes=payload, mime_type=mime_type),
            reference_id=reference_id,
        )

    def _build_content_image_part(self, *, sdk_types, object_key: str) -> object:
        """Build a GenAI content image part from an object-storage artifact."""
        payload = self._object_storage.get_bytes(object_key)
        mime_type = self._guess_mime_type(object_key=object_key, fallback="image/png")
        return sdk_types.Part.from_bytes(data=payload, mime_type=mime_type)

    def _require_client(self) -> object:
        """Return the injected SDK client or lazily construct the Google GenAI client."""
        if self._client is None:
            genai = self._require_genai_module()
            self._client = genai.Client(vertexai=True, project=self._project, location=self._location)
        return self._client

    @staticmethod
    def _require_genai_module():
        """Import google.genai lazily so app startup does not load the SDK eagerly."""
        if importlib.util.find_spec("google.genai") is None:
            raise RuntimeError("google-genai SDK is not installed")
        return importlib.import_module("google.genai")

    @staticmethod
    def _require_sdk_types():
        """Import google.genai.types lazily for typed image-edit requests."""
        if importlib.util.find_spec("google.genai.types") is None:
            raise RuntimeError("google-genai SDK types are not installed")
        return importlib.import_module("google.genai.types")

    @staticmethod
    def _extract_first_image(response: object) -> tuple[bytes, str]:
        """Extract the first generated image bytes from the SDK-shaped response."""
        generated_images = getattr(response, "generated_images", None)
        if not isinstance(generated_images, list) or not generated_images:
            raise RuntimeError("google_genai_image_editing_returned_no_generated_images")
        first_image = getattr(generated_images[0], "image", None)
        image_bytes = getattr(first_image, "image_bytes", None) if first_image is not None else None
        mime_type = getattr(first_image, "mime_type", None) if first_image is not None else None
        if not isinstance(image_bytes, bytes) or not image_bytes:
            raise RuntimeError("google_genai_image_editing_returned_no_image_bytes")
        if not isinstance(mime_type, str) or not mime_type:
            raise RuntimeError("google_genai_image_editing_returned_no_mime_type")
        return image_bytes, mime_type

    @staticmethod
    def _extract_first_inline_image(response: object, *, fallback_mime_type: str) -> tuple[bytes, str]:
        """Extract the first inline image part from a Gemini native image response."""
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                inline_data = getattr(part, "inline_data", None)
                image_bytes = getattr(inline_data, "data", None) if inline_data is not None else None
                if not isinstance(image_bytes, bytes) or not image_bytes:
                    continue
                mime_type = getattr(inline_data, "mime_type", None) or fallback_mime_type
                if not isinstance(mime_type, str) or not mime_type:
                    mime_type = fallback_mime_type
                return image_bytes, mime_type
        raise RuntimeError("google_genai_image_editing_returned_no_inline_image")

    def _build_output_object_key(self, *, task: str, mime_type: str) -> str:
        """Build a backend-owned object key for provider-produced edited bytes."""
        extension = mimetypes.guess_extension(mime_type) or ".bin"
        filename = normalize_storage_filename(filename=f"{uuid4().hex}{extension}", fallback="edited-image.bin")
        safe_task = normalize_storage_filename(filename=task, fallback="image-editing")
        return "/".join(
            [
                self._root_prefix,
                "provider-artifacts",
                "image-editing",
                safe_task,
                filename,
            ]
        )

    @staticmethod
    def _guess_mime_type(*, object_key: str, fallback: str) -> str:
        """Infer the MIME type from the object key and fall back to the requested output type."""
        guessed, _encoding = mimetypes.guess_type(object_key)
        return guessed or fallback

    def _uses_gemini_native_image_model(self) -> bool:
        """Detect Gemini image models that use generate_content instead of edit_image."""
        normalized_model = self._model.strip().lower()
        return normalized_model.startswith("gemini-") and "image" in normalized_model
