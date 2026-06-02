"""Deployment and runtime configuration for the FitFabrica repair agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RepairAgentDeployConfig:
    """Immutable deployment configuration for the repair instruction ADK runtime."""

    name: str = "repair_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica repair instruction agent."
