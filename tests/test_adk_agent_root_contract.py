from __future__ import annotations

from google.adk.agents import BaseAgent

from src.adk_agents.daily_memory_agent.agent import root_agent as daily_root_agent
from src.adk_agents.rolling_memory_agent.agent import root_agent as rolling_root_agent
from src.adk_agents.primary_agent.agent import root_agent as primary_root_agent


def test_primary_agent_exports_base_agent_root() -> None:
    assert isinstance(primary_root_agent, BaseAgent)


def test_daily_memory_agent_exports_base_agent_root() -> None:
    assert isinstance(daily_root_agent, BaseAgent)


def test_rolling_memory_agent_exports_base_agent_root() -> None:
    assert isinstance(rolling_root_agent, BaseAgent)
