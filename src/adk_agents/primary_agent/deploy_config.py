"""Deployment and runtime configuration for the Primary ADK agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PrimaryAgentDeployConfig:
    """Immutable deployment configuration for the Primary ADK runtime."""

    name: str = "primary_agent"
    model: str = "gemini-2.5-flash"
    description: str = "Primary agent runtime."
