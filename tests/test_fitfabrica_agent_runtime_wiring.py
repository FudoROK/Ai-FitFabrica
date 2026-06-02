from __future__ import annotations

from types import SimpleNamespace

from google.adk.agents import BaseAgent

from src.entrypoints import runtime_dependencies as deps


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        environment="test",
        try_on_allowed_content_types=["image/jpeg", "image/png"],
        try_on_max_upload_bytes=10 * 1024 * 1024,
        object_storage_prefix="fitfabrica",
        object_storage_signed_url_ttl_seconds=900,
        try_on_generation_backend="sandbox_fake",
        try_on_quality_verifier_backend="model_backed",
        try_on_repair_backend="provider_runtime",
        try_on_stylist_backend="model_backed",
        default_person_credit_account_id="public-person",
        billing_core_enabled=False,
    )


def test_fitfabrica_agent_runtime_dependencies_are_cached_per_settings_instance(monkeypatch) -> None:
    settings = _settings()
    provider_runtime = object()
    monkeypatch.setattr(deps, "provider_runtime", lambda _settings: provider_runtime)

    first = deps.fitfabrica_agent_runtime_dependencies(settings)
    second = deps.fitfabrica_agent_runtime_dependencies(settings)

    assert first is second
    assert first.provider_runtime is provider_runtime


def test_fitfabrica_agent_runtime_dependencies_expose_product_agent_roots(monkeypatch) -> None:
    settings = _settings()
    monkeypatch.setattr(deps, "provider_runtime", lambda _settings: object())

    runtime = deps.fitfabrica_agent_runtime_dependencies(settings)

    assert isinstance(runtime.orchestrator_agent, BaseAgent)
    assert isinstance(runtime.user_profile_agent, BaseAgent)
    assert isinstance(runtime.business_profile_agent, BaseAgent)
    assert isinstance(runtime.human_identity_agent, BaseAgent)
    assert isinstance(runtime.garment_identity_agent, BaseAgent)
    assert isinstance(runtime.material_texture_agent, BaseAgent)
    assert isinstance(runtime.try_on_agent, BaseAgent)
    assert isinstance(runtime.quality_verifier_agent, BaseAgent)
    assert isinstance(runtime.repair_agent, BaseAgent)
    assert isinstance(runtime.fashion_stylist_agent, BaseAgent)
    assert isinstance(runtime.marketplace_agent, BaseAgent)
    assert isinstance(runtime.trend_agent, BaseAgent)
    assert isinstance(runtime.pricing_agent, BaseAgent)
    assert isinstance(runtime.product_card_agent, BaseAgent)
    assert isinstance(runtime.cost_credits_agent, BaseAgent)
    assert runtime.orchestrator_deploy_config.name == "orchestrator_agent"
    assert runtime.user_profile_deploy_config.name == "user_profile_agent"
    assert runtime.business_profile_deploy_config.name == "business_profile_agent"
    assert runtime.try_on_deploy_config.name == "try_on_agent"
    assert runtime.quality_verifier_deploy_config.name == "quality_verifier_agent"
    assert runtime.marketplace_deploy_config.name == "marketplace_agent"
    assert runtime.trend_deploy_config.name == "trend_agent"
    assert runtime.pricing_deploy_config.name == "pricing_agent"
    assert runtime.product_card_deploy_config.name == "product_card_agent"
    assert runtime.cost_credits_deploy_config.name == "cost_credits_agent"


def test_try_on_runtime_dependencies_remain_backend_owned_after_agent_bundle_is_added(monkeypatch) -> None:
    settings = _settings()
    providers = SimpleNamespace(
        structured_reasoning=None,
        image_editing=None,
        embedding_provider=None,
        image_generation=None,
        agent_runtime=None,
    )
    infrastructure = SimpleNamespace(
        sql_session_factory=None,
        object_storage=object(),
        redis_client=None,
    )
    monkeypatch.setattr(deps, "provider_runtime", lambda _settings: providers)
    monkeypatch.setattr(deps, "portable_infrastructure", lambda _settings: infrastructure)

    runtime = deps.try_on_runtime_dependencies(settings)

    assert runtime.workflow_service.__class__.__name__ == "TryOnWorkflowService"
    assert runtime.generation_adapter.__class__.__name__ == "FakeTryOnGenerationAdapter"
    assert runtime.quality_verifier.__class__.__name__ == "DeterministicTryOnQualityVerifier"
