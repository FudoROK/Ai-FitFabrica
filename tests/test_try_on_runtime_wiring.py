from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps


def _settings(environment: str = "test"):
    return SimpleNamespace(
        environment=environment,
        llm=SimpleNamespace(provider="fake"),
        ingress_rate_limit_max_events=20,
        ingress_rate_limit_window_seconds=60,
        ingress_rate_limit_collection="ingress_rate_limits",
        ingress_global_safety_cap_max_events=2000,
        object_storage_prefix="fitfabrica",
        object_storage_signed_url_ttl_seconds=900,
        try_on_allowed_content_types=["image/jpeg", "image/png", "image/webp"],
        try_on_max_upload_bytes=1024,
        billing_core_enabled=False,
        try_on_generation_backend="sandbox_fake",
        enable_real_try_on_generation=False,
        try_on_vertex_failure_fallback_backend="none",
        try_on_quality_verifier_backend="model_backed",
        try_on_repair_backend="provider_runtime",
        try_on_stylist_backend="model_backed",
    )


def test_try_on_runtime_dependencies_prefer_sql_when_portable_sql_exists(monkeypatch):
    settings = _settings(environment="prod")
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage="storage"),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.job_repository.__class__.__name__ == "SqlTryOnJobRepository"
    assert runtime.workflow_service._repository is runtime.job_repository
    assert runtime.human_identity_analyzer.__class__.__name__ == "HumanIdentityAnalysisAdapter"
    assert runtime.garment_identity_analyzer.__class__.__name__ == "TryOnGarmentIdentityAnalysisAdapter"
    assert runtime.garment_identity_analyzer._taxonomy_service.__class__.__name__ == "GarmentTaxonomyService"
    assert runtime.material_texture_analyzer.__class__.__name__ == "TryOnMaterialTextureAnalysisAdapter"
    assert runtime.analysis_bundle_service.__class__.__name__ == "TryOnAnalysisBundleService"
    assert runtime.quality_verifier.__class__.__name__ == "TryOnQualityVerifierAgentAdapter"
    assert runtime.quality_verifier._preferred_model == "gemini-2.5-flash"
    assert runtime.repair_adapter.__class__.__name__ == "ProviderRuntimeTryOnRepairAdapter"
    assert runtime.repair_adapter._repair_instruction_planner.__class__.__name__ == "TryOnRepairAgentPlanner"
    assert runtime.repair_adapter._repair_instruction_planner._preferred_model == "gemini-2.5-flash"
    assert runtime.stylist_adapter.__class__.__name__ == "ModelBackedTryOnStylist"


def test_try_on_runtime_dependencies_are_cached(monkeypatch):
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage="storage"),
    )

    first = deps.try_on_runtime_dependencies(settings)
    second = deps.try_on_runtime_dependencies(settings)

    assert first is second
    assert first.garment_identity_analyzer.__class__.__name__ == "DeterministicTryOnGarmentIdentityAnalysisAdapter"
    assert first.material_texture_analyzer.__class__.__name__ == "DeterministicTryOnMaterialTextureAnalysisAdapter"


def test_try_on_runtime_dependencies_can_select_provider_runtime_generation(monkeypatch):
    settings = _settings()
    settings.try_on_generation_backend = "provider_runtime"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(image_editing=object()),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.generation_adapter.__class__.__name__ == "TryOnProviderGenerationAdapter"


def test_try_on_runtime_dependencies_can_select_vertex_virtual_try_on_generation(monkeypatch):
    settings = _settings()
    settings.try_on_generation_backend = "vertex_virtual_try_on"
    settings.enable_real_try_on_generation = True
    settings.vertex_project = "fitfabrica-test"
    settings.vertex_virtual_try_on_location = "global"
    settings.vertex_virtual_try_on_model = "virtual-try-on-001"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "VertexVirtualTryOnClient",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.generation_adapter.__class__.__name__ == "VertexVirtualTryOnGenerationAdapter"


def test_try_on_runtime_dependencies_disable_stub_repair_for_real_vertex_generation(monkeypatch):
    settings = _settings(environment="prod")
    settings.try_on_generation_backend = "vertex_virtual_try_on"
    settings.enable_real_try_on_generation = True
    settings.vertex_project = "fitfabrica-test"
    settings.vertex_virtual_try_on_location = "global"
    settings.vertex_virtual_try_on_model = "virtual-try-on-001"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(
            agent_runtime=object(),
            image_editing=SimpleNamespace(provider_name="stub_image_editing"),
            structured_reasoning=None,
            embedding_provider=None,
        ),
    )
    monkeypatch.setattr(
        deps,
        "VertexVirtualTryOnClient",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.generation_adapter.__class__.__name__ == "VertexVirtualTryOnGenerationAdapter"
    assert runtime.repair_adapter is None


def test_try_on_runtime_dependencies_allow_provider_repair_for_real_vertex_generation(monkeypatch):
    settings = _settings(environment="prod")
    settings.try_on_generation_backend = "vertex_virtual_try_on"
    settings.enable_real_try_on_generation = True
    settings.vertex_project = "fitfabrica-test"
    settings.vertex_virtual_try_on_location = "global"
    settings.vertex_virtual_try_on_model = "virtual-try-on-001"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(
            agent_runtime=object(),
            image_editing=SimpleNamespace(provider_name="google_genai_image_editing"),
            structured_reasoning=None,
            embedding_provider=None,
        ),
    )
    monkeypatch.setattr(
        deps,
        "VertexVirtualTryOnClient",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.generation_adapter.__class__.__name__ == "VertexVirtualTryOnGenerationAdapter"
    assert runtime.repair_adapter.__class__.__name__ == "ProviderRuntimeTryOnRepairAdapter"
    assert runtime.repair_adapter._repair_instruction_planner.__class__.__name__ == "TryOnRepairAgentPlanner"


def test_try_on_runtime_dependencies_disable_deterministic_repair_for_real_vertex_generation(monkeypatch):
    settings = _settings(environment="prod")
    settings.try_on_generation_backend = "vertex_virtual_try_on"
    settings.try_on_repair_backend = "deterministic"
    settings.enable_real_try_on_generation = True
    settings.vertex_project = "fitfabrica-test"
    settings.vertex_virtual_try_on_location = "global"
    settings.vertex_virtual_try_on_model = "virtual-try-on-001"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory="session-factory", object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(
            agent_runtime=object(),
            image_editing=SimpleNamespace(provider_name="stub_image_editing"),
            structured_reasoning=None,
            embedding_provider=None,
        ),
    )
    monkeypatch.setattr(
        deps,
        "VertexVirtualTryOnClient",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.generation_adapter.__class__.__name__ == "VertexVirtualTryOnGenerationAdapter"
    assert runtime.repair_adapter is None


def test_try_on_runtime_dependencies_can_wrap_vertex_generation_with_provider_fallback(monkeypatch):
    settings = _settings()
    settings.try_on_generation_backend = "vertex_virtual_try_on"
    settings.enable_real_try_on_generation = True
    settings.try_on_vertex_failure_fallback_backend = "provider_runtime"
    settings.vertex_project = "fitfabrica-test"
    settings.vertex_virtual_try_on_location = "global"
    settings.vertex_virtual_try_on_model = "virtual-try-on-001"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(image_editing=object()),
    )
    monkeypatch.setattr(
        deps,
        "VertexVirtualTryOnClient",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.generation_adapter.__class__.__name__ == "FallbackTryOnGenerationAdapter"


def test_try_on_runtime_dependencies_reject_missing_provider_fallback_runtime(monkeypatch):
    settings = _settings()
    settings.try_on_generation_backend = "vertex_virtual_try_on"
    settings.enable_real_try_on_generation = True
    settings.try_on_vertex_failure_fallback_backend = "provider_runtime"
    settings.vertex_project = "fitfabrica-test"
    settings.vertex_virtual_try_on_location = "global"
    settings.vertex_virtual_try_on_model = "virtual-try-on-001"
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage="storage"),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(image_editing=None),
    )
    monkeypatch.setattr(
        deps,
        "VertexVirtualTryOnClient",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    import pytest

    with pytest.raises(RuntimeError, match="provider runtime"):
        deps.try_on_runtime_dependencies(settings)


def test_operations_runtime_registers_try_on_worker_handler(monkeypatch):
    settings = _settings()
    monkeypatch.setattr(
        deps,
        "portable_infrastructure",
        lambda _settings: SimpleNamespace(sql_session_factory=None, object_storage="storage", redis_client=None),
    )
    monkeypatch.setattr(
        deps,
        "provider_runtime",
        lambda _settings: SimpleNamespace(image_editing=None),
    )

    runtime = deps.operations_runtime_dependencies(settings)

    assert "try_on" in runtime.worker_runtime._handlers
