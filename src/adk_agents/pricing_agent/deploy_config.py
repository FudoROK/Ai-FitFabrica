"""Deployment and runtime configuration for the FitFabrica pricing agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PricingAgentDeployConfig:
    """Immutable deployment configuration for the pricing ADK runtime."""

    name: str = "pricing_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica pricing explanation agent."
