"""Backend-owned provider runtime composition and selection."""

from __future__ import annotations

from dataclasses import dataclass

from src.adapters.ai import FakeEmbeddingProvider, StubImageEditingProvider, StubImageGenerationProvider
from src.adapters.vector.namespaces import namespace_spec
from src.adapters.storage.contracts import ObjectStorage
from src.domain.vector_search import VectorNamespace
from src.domain.provider_ports import (
    AgentRuntimePort,
    EmbeddingProviderPort,
    ImageEditingPort,
    ImageGenerationPort,
    StructuredReasoningPort,
)
from src.llm.providers.fake_provider import FakeProvider


@dataclass(frozen=True)
class ProviderRuntime:
    """Composed provider runtime owned by backend wiring."""

    structured_reasoning: StructuredReasoningPort | None
    agent_runtime: AgentRuntimePort | None
    embedding_provider: EmbeddingProviderPort | None
    image_generation: ImageGenerationPort | None
    image_editing: ImageEditingPort | None


def build_provider_runtime(settings, *, object_storage: ObjectStorage | None = None) -> ProviderRuntime:
    """Build provider runtime adapters from settings without leaking selection into business code."""
    llm_settings = getattr(settings, "llm", None)
    provider_name = (getattr(llm_settings, "provider", "fake") or "fake").strip().lower()
    embedding_provider = FakeEmbeddingProvider(vector_size=namespace_spec(VectorNamespace.PRODUCTS).vector_size)
    image_generation = StubImageGenerationProvider()
    image_editing = _build_image_editing_provider(settings, object_storage=object_storage)

    if provider_name == "fake":
        fake_provider = FakeProvider()
        return ProviderRuntime(
            structured_reasoning=fake_provider,
            agent_runtime=fake_provider,
            embedding_provider=embedding_provider,
            image_generation=image_generation,
            image_editing=image_editing,
        )

    if provider_name == "gemini_structured":
        from src.llm.providers.gemini_structured_provider import GeminiStructuredProvider

        provider = GeminiStructuredProvider(settings=settings)
        return ProviderRuntime(
            structured_reasoning=provider,
            agent_runtime=provider,
            embedding_provider=embedding_provider,
            image_generation=image_generation,
            image_editing=image_editing,
        )

    if provider_name == "vertex":
        from src.llm.providers.gemini_structured_provider import GeminiStructuredProvider

        provider = GeminiStructuredProvider(settings=settings)
        return ProviderRuntime(
            structured_reasoning=provider,
            agent_runtime=provider,
            embedding_provider=embedding_provider,
            image_generation=image_generation,
            image_editing=image_editing,
        )

    raise ValueError(f"Unsupported provider runtime: {provider_name}")


def _build_image_editing_provider(settings, *, object_storage: ObjectStorage | None) -> ImageEditingPort:
    """Build image editing adapter from explicit provider settings."""
    provider_name = (getattr(settings, "image_editing_provider", "stub") or "stub").strip().lower()
    if provider_name == "stub":
        return StubImageEditingProvider()
    if provider_name == "google_genai":
        return _build_google_genai_image_editing_provider(settings, object_storage=object_storage)
    raise ValueError(f"Unsupported image editing provider: {provider_name}")


def _build_google_genai_image_editing_provider(
    settings,
    *,
    object_storage: ObjectStorage | None = None,
) -> ImageEditingPort:
    """Build the Google GenAI image-editing adapter lazily."""
    if object_storage is None:
        raise RuntimeError("IMAGE_EDITING_PROVIDER=google_genai requires object storage runtime")
    model = (getattr(settings, "image_editing_model", None) or "").strip()
    if not model:
        raise RuntimeError("IMAGE_EDITING_MODEL is required when IMAGE_EDITING_PROVIDER=google_genai")
    project = (getattr(settings, "vertex_project", None) or getattr(getattr(settings, "llm", None), "vertex_project", None) or "").strip()
    if not project:
        raise RuntimeError("VERTEX_PROJECT is required when IMAGE_EDITING_PROVIDER=google_genai")
    location = (
        getattr(settings, "vertex_location", None)
        or getattr(getattr(settings, "llm", None), "vertex_location", None)
        or "us-central1"
    )
    from src.adapters.ai.google_genai_image_editing import GoogleGenAIImageEditingProvider

    return GoogleGenAIImageEditingProvider(
        project=project,
        location=location,
        model=model,
        object_storage=object_storage,
        root_prefix=getattr(settings, "image_editing_root_prefix", "fitfabrica"),
    )
