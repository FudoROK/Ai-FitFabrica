"""Deployment and runtime configuration for the rolling memory ADK agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RollingMemoryDeployConfig:
    """Immutable deployment configuration for the rolling memory ADK runtime."""

    name: str = "memory_rolling_agent"
    model: str = "gemini-2.5-flash"
    description: str = "Rolling memory runtime agent."
