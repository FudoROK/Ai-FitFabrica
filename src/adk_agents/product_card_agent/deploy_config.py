"""Deployment and runtime configuration for the FitFabrica product card agent."""

from dataclasses import dataclass

from .prompt_config import CONTRACT_VERSION, PROMPT_VERSION


@dataclass(frozen=True)
class ProductCardAgentDeployConfig:
    """Immutable deployment configuration for the product-card ADK runtime."""

    name: str = "product_card_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica product-card content drafting agent."
    prompt_version: str = PROMPT_VERSION
    contract_version: str = CONTRACT_VERSION
    output_repair_policy: str = "transport_only"
    semantic_failure_policy: str = "reject"
