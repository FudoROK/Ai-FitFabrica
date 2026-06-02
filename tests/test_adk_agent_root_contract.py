from __future__ import annotations

from google.adk.agents import BaseAgent

from src.adk_agents.business_profile_agent.agent import root_agent as business_profile_root_agent
from src.adk_agents.cost_credits_agent.agent import root_agent as cost_credits_root_agent
from src.adk_agents.daily_memory_agent.agent import root_agent as daily_root_agent
from src.adk_agents.fashion_stylist_agent.agent import root_agent as fashion_stylist_root_agent
from src.adk_agents.garment_identity_agent.agent import root_agent as garment_identity_root_agent
from src.adk_agents.human_identity_agent.agent import root_agent as human_identity_root_agent
from src.adk_agents.marketplace_agent.agent import root_agent as marketplace_root_agent
from src.adk_agents.material_texture_agent.agent import root_agent as material_texture_root_agent
from src.adk_agents.orchestrator_agent.agent import root_agent as orchestrator_root_agent
from src.adk_agents.pricing_agent.agent import root_agent as pricing_root_agent
from src.adk_agents.product_card_agent.agent import root_agent as product_card_root_agent
from src.adk_agents.quality_verifier_agent.agent import root_agent as quality_verifier_root_agent
from src.adk_agents.repair_agent.agent import root_agent as repair_root_agent
from src.adk_agents.rolling_memory_agent.agent import root_agent as rolling_root_agent
from src.adk_agents.trend_agent.agent import root_agent as trend_root_agent
from src.adk_agents.try_on_agent.agent import root_agent as try_on_root_agent
from src.adk_agents.user_profile_agent.agent import root_agent as user_profile_root_agent


def test_orchestrator_agent_exports_base_agent_root() -> None:
    assert isinstance(orchestrator_root_agent, BaseAgent)


def test_user_profile_agent_exports_base_agent_root() -> None:
    assert isinstance(user_profile_root_agent, BaseAgent)


def test_business_profile_agent_exports_base_agent_root() -> None:
    assert isinstance(business_profile_root_agent, BaseAgent)


def test_human_identity_agent_exports_base_agent_root() -> None:
    assert isinstance(human_identity_root_agent, BaseAgent)


def test_garment_identity_agent_exports_base_agent_root() -> None:
    assert isinstance(garment_identity_root_agent, BaseAgent)


def test_material_texture_agent_exports_base_agent_root() -> None:
    assert isinstance(material_texture_root_agent, BaseAgent)


def test_try_on_agent_exports_base_agent_root() -> None:
    assert isinstance(try_on_root_agent, BaseAgent)


def test_quality_verifier_agent_exports_base_agent_root() -> None:
    assert isinstance(quality_verifier_root_agent, BaseAgent)


def test_repair_agent_exports_base_agent_root() -> None:
    assert isinstance(repair_root_agent, BaseAgent)


def test_fashion_stylist_agent_exports_base_agent_root() -> None:
    assert isinstance(fashion_stylist_root_agent, BaseAgent)


def test_marketplace_agent_exports_base_agent_root() -> None:
    assert isinstance(marketplace_root_agent, BaseAgent)


def test_trend_agent_exports_base_agent_root() -> None:
    assert isinstance(trend_root_agent, BaseAgent)


def test_pricing_agent_exports_base_agent_root() -> None:
    assert isinstance(pricing_root_agent, BaseAgent)


def test_product_card_agent_exports_base_agent_root() -> None:
    assert isinstance(product_card_root_agent, BaseAgent)


def test_cost_credits_agent_exports_base_agent_root() -> None:
    assert isinstance(cost_credits_root_agent, BaseAgent)


def test_daily_memory_agent_exports_base_agent_root() -> None:
    assert isinstance(daily_root_agent, BaseAgent)


def test_rolling_memory_agent_exports_base_agent_root() -> None:
    assert isinstance(rolling_root_agent, BaseAgent)
