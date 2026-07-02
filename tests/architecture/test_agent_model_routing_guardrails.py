from __future__ import annotations

from pathlib import Path


def test_runtime_builders_use_central_agent_model_routing() -> None:
    workflow_builder = Path("src/entrypoints/runtime_dependency_workflow_builders.py").read_text(encoding="utf-8")
    product_card_builder = Path("src/entrypoints/runtime_dependency_product_card_builder.py").read_text(encoding="utf-8")

    assert "resolve_agent_preferred_model" in workflow_builder
    assert "resolve_agent_preferred_model" in product_card_builder
    assert "try_on_quality_verifier_preferred_model" in workflow_builder
    assert "product_card_agent_preferred_model" in product_card_builder


def test_model_routing_policy_covers_current_product_agent_invocations() -> None:
    policy = Path("src/llm/agent_model_routing.py").read_text(encoding="utf-8")

    for agent_name in (
        "human_identity_agent",
        "garment_identity_agent",
        "material_texture_agent",
        "try_on_agent",
        "quality_verifier_agent",
        "repair_agent",
        "product_card_agent",
    ):
        assert agent_name in policy
