"""Deployment and runtime configuration for the daily memory ADK agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyMemoryDeployConfig:
    """Immutable deployment configuration for the daily memory ADK runtime."""

    name: str = "memory_daily_agent"
    model: str = "gemini-2.5-flash"
    description: str = "Daily memory runtime agent."
