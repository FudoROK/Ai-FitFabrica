from __future__ import annotations

from dataclasses import dataclass

from src.llm.provider_runtime import ProviderRuntime, build_provider_runtime
from src.adapters.vector.namespaces import namespace_spec
from src.domain.provider_models import EmbeddingRequest
from src.domain.vector_search import VectorNamespace


@dataclass
class _LLM:
    provider: str
    vertex_project: str | None = None
    vertex_location: str | None = "us-central1"
    model: str = "test-model"
    vertex_agent_resource: str | None = None
    vertex_memory_daily_agent_resource: str | None = None
    vertex_memory_rolling_agent_resource: str | None = None


@dataclass
class _Settings:
    llm: _LLM
    image_editing_provider: str = "stub"
    image_editing_model: str = "imagen-edit-test"
    image_editing_root_prefix: str = "fitfabrica-test"


def test_provider_runtime_exposes_structured_reasoning_and_agent_runtime_ports() -> None:
    runtime = ProviderRuntime(
        structured_reasoning=object(),
        agent_runtime=object(),
        embedding_provider=object(),
        image_generation=object(),
        image_editing=object(),
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is not None


def test_registry_builds_multimodal_agent_runtime_provider_for_gemini_structured() -> None:
    runtime = build_provider_runtime(
        _Settings(
            llm=_LLM(
                provider="gemini_structured",
                vertex_project="project-id",
            )
        )
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is runtime.structured_reasoning
    assert runtime.agent_runtime.provider_name == "gemini_structured"
    assert runtime.agent_runtime.supports_artifacts is True


def test_provider_runtime_embedding_size_matches_products_vector_namespace() -> None:
    runtime = build_provider_runtime(_Settings(llm=_LLM(provider="fake")))

    result = runtime.embedding_provider.embed(
        EmbeddingRequest(namespace=VectorNamespace.PRODUCTS.value, input_text="white shirt")
    )

    assert len(result.embedding) == namespace_spec(VectorNamespace.PRODUCTS).vector_size


def test_registry_builds_agent_runtime_provider_for_vertex() -> None:
    runtime = build_provider_runtime(
        _Settings(
            llm=_LLM(
                provider="vertex",
                vertex_project="project-id",
                vertex_agent_resource="projects/p/locations/us-central1/reasoningEngines/1",
            )
        )
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is not None
    assert runtime.agent_runtime.provider_name == "gemini_structured"
    assert runtime.agent_runtime.supports_artifacts is True


def test_registry_can_wire_google_genai_image_editing_provider_for_vertex(monkeypatch) -> None:
    class _EditingProvider:
        provider_name = "google_genai_image_editing"

        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    monkeypatch.setattr(
        "src.llm.provider_runtime._build_google_genai_image_editing_provider",
        lambda settings, object_storage=None: _EditingProvider(settings=settings, object_storage=object_storage),
    )

    runtime = build_provider_runtime(
        _Settings(
            llm=_LLM(
                provider="vertex",
                vertex_project="project-id",
                vertex_agent_resource="projects/p/locations/us-central1/reasoningEngines/1",
            ),
            image_editing_provider="google_genai",
        )
    )

    assert runtime.image_editing is not None
    assert runtime.image_editing.provider_name == "google_genai_image_editing"
