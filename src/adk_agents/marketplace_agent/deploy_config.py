"""Deployment and runtime configuration for the FitFabrica marketplace agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketplaceAgentDeployConfig:
    """Immutable deployment configuration for the marketplace ADK runtime."""

    name: str = "marketplace_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica marketplace retrieval guidance agent."
