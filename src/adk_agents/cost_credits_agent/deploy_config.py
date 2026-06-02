"""Deployment and runtime configuration for the FitFabrica cost and credits agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CostCreditsAgentDeployConfig:
    """Immutable deployment configuration for the cost/credits ADK runtime."""

    name: str = "cost_credits_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica cost and credits explanation agent."
