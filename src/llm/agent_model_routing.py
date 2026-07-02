"""Central model routing policy for FitFabrica product agents."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AgentTaskKind = Literal[
    "text_generation",
    "visual_analysis",
    "visual_quality_verification",
    "repair_instruction",
    "marketplace_reasoning",
]
RiskTier = Literal["low", "medium", "high"]
CostTier = Literal["low", "medium", "high"]


class AgentModelRoute(BaseModel):
    """One backend-owned model selection decision for an agent invocation."""

    model_config = ConfigDict(extra="forbid")

    agent_name: str = Field(min_length=1)
    task_kind: AgentTaskKind
    risk_tier: RiskTier
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    max_cost_tier: CostTier
    requires_vision: bool = False
    override_source: Literal["policy", "explicit_setting"] = "policy"


_ROUTES: dict[tuple[str, AgentTaskKind, RiskTier], AgentModelRoute] = {
    ("human_identity_agent", "visual_analysis", "high"): AgentModelRoute(
        agent_name="human_identity_agent",
        task_kind="visual_analysis",
        risk_tier="high",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
        requires_vision=True,
    ),
    ("garment_identity_agent", "visual_analysis", "medium"): AgentModelRoute(
        agent_name="garment_identity_agent",
        task_kind="visual_analysis",
        risk_tier="medium",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
        requires_vision=True,
    ),
    ("material_texture_agent", "visual_analysis", "medium"): AgentModelRoute(
        agent_name="material_texture_agent",
        task_kind="visual_analysis",
        risk_tier="medium",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
        requires_vision=True,
    ),
    ("try_on_agent", "text_generation", "medium"): AgentModelRoute(
        agent_name="try_on_agent",
        task_kind="text_generation",
        risk_tier="medium",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
    ),
    ("quality_verifier_agent", "visual_quality_verification", "high"): AgentModelRoute(
        agent_name="quality_verifier_agent",
        task_kind="visual_quality_verification",
        risk_tier="high",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
        requires_vision=True,
    ),
    ("repair_agent", "repair_instruction", "medium"): AgentModelRoute(
        agent_name="repair_agent",
        task_kind="repair_instruction",
        risk_tier="medium",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
        requires_vision=True,
    ),
    ("product_card_agent", "text_generation", "low"): AgentModelRoute(
        agent_name="product_card_agent",
        task_kind="text_generation",
        risk_tier="low",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        max_cost_tier="low",
    ),
    ("fashion_stylist_agent", "text_generation", "low"): AgentModelRoute(
        agent_name="fashion_stylist_agent",
        task_kind="text_generation",
        risk_tier="low",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        max_cost_tier="low",
    ),
    ("marketplace_agent", "marketplace_reasoning", "medium"): AgentModelRoute(
        agent_name="marketplace_agent",
        task_kind="marketplace_reasoning",
        risk_tier="medium",
        provider="gemini",
        model="gemini-2.5-flash",
        max_cost_tier="medium",
    ),
    ("pricing_agent", "text_generation", "low"): AgentModelRoute(
        agent_name="pricing_agent",
        task_kind="text_generation",
        risk_tier="low",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        max_cost_tier="low",
    ),
    ("cost_credits_agent", "text_generation", "low"): AgentModelRoute(
        agent_name="cost_credits_agent",
        task_kind="text_generation",
        risk_tier="low",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        max_cost_tier="low",
    ),
}


def resolve_agent_model_route(
    *,
    agent_name: str,
    task_kind: AgentTaskKind,
    risk_tier: RiskTier,
    explicit_model: str | None = None,
) -> AgentModelRoute:
    """Return the configured model route, preserving explicit env/settings overrides."""

    key = (agent_name, task_kind, risk_tier)
    if key not in _ROUTES:
        raise KeyError(f"Unknown agent model route: {agent_name}/{task_kind}/{risk_tier}")
    route = _ROUTES[key]
    if explicit_model is None or not explicit_model.strip():
        return route
    return route.model_copy(update={"model": explicit_model.strip(), "override_source": "explicit_setting"})


def resolve_agent_preferred_model(
    *,
    agent_name: str,
    task_kind: AgentTaskKind,
    risk_tier: RiskTier,
    explicit_model: str | None = None,
) -> str:
    """Return only the selected model string for runtime adapters."""

    return resolve_agent_model_route(
        agent_name=agent_name,
        task_kind=task_kind,
        risk_tier=risk_tier,
        explicit_model=explicit_model,
    ).model
