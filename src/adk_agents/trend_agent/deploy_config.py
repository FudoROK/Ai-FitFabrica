"""Deployment and runtime configuration for the FitFabrica trend agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrendAgentDeployConfig:
    """Immutable deployment configuration for the trend ADK runtime."""

    name: str = "trend_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica trend interpretation agent."
