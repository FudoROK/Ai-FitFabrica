from __future__ import annotations

import pytest

from src.llm.agent_model_routing import resolve_agent_model_route


def test_agent_model_routing_uses_cheap_tier_for_product_card_text() -> None:
    route = resolve_agent_model_route(
        agent_name="product_card_agent",
        task_kind="text_generation",
        risk_tier="low",
    )

    assert route.provider == "gemini"
    assert route.model == "gemini-2.5-flash-lite"
    assert route.max_cost_tier == "low"


def test_agent_model_routing_uses_visual_tier_for_quality_verifier() -> None:
    route = resolve_agent_model_route(
        agent_name="quality_verifier_agent",
        task_kind="visual_quality_verification",
        risk_tier="high",
    )

    assert route.provider == "gemini"
    assert route.model == "gemini-2.5-flash"
    assert route.requires_vision is True
    assert route.max_cost_tier == "medium"


def test_agent_model_routing_allows_explicit_safe_override() -> None:
    route = resolve_agent_model_route(
        agent_name="quality_verifier_agent",
        task_kind="visual_quality_verification",
        risk_tier="high",
        explicit_model="gemini-2.5-pro",
    )

    assert route.model == "gemini-2.5-pro"
    assert route.override_source == "explicit_setting"


def test_agent_model_routing_rejects_unknown_route() -> None:
    with pytest.raises(KeyError, match="Unknown agent model route"):
        resolve_agent_model_route(
            agent_name="unknown_agent",
            task_kind="text_generation",
            risk_tier="low",
        )
