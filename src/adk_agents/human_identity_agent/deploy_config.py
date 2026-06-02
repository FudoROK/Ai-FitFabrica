"""Deployment and runtime configuration for the FitFabrica human identity agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HumanIdentityAgentDeployConfig:
    """Immutable deployment configuration for the human identity ADK runtime."""

    name: str = "human_identity_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica human identity preservation agent."
