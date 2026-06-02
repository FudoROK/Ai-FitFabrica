"""Deployment and runtime configuration for the FitFabrica Try-On agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TryOnAgentDeployConfig:
    """Immutable deployment configuration for the Try-On instruction ADK runtime."""

    name: str = "try_on_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica Try-On instruction agent."
