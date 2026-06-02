"""Deployment and runtime configuration for the FitFabrica fashion stylist agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FashionStylistAgentDeployConfig:
    """Immutable deployment configuration for the fashion stylist ADK runtime."""

    name: str = "fashion_stylist_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica fashion stylist explanation agent."
