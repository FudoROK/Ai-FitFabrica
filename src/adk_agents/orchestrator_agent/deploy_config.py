"""Deployment and runtime configuration for the FitFabrica orchestrator agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OrchestratorAgentDeployConfig:
    """Immutable deployment configuration for the orchestrator ADK runtime."""

    name: str = "orchestrator_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica workflow routing agent."
