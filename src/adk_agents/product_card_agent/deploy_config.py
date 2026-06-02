"""Deployment and runtime configuration for the FitFabrica product card agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductCardAgentDeployConfig:
    """Immutable deployment configuration for the product-card ADK runtime."""

    name: str = "product_card_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica product-card content drafting agent."
