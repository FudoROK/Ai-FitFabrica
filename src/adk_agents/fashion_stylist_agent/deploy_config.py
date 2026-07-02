"""Deployment and runtime configuration for the FitFabrica fashion stylist agent."""

from dataclasses import dataclass

from .prompt_config import CONTRACT_VERSION, PROMPT_VERSION


@dataclass(frozen=True)
class FashionStylistAgentDeployConfig:
    """Immutable deployment configuration for the fashion stylist ADK runtime."""

    name: str = "fashion_stylist_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica fashion stylist explanation agent."
    prompt_version: str = PROMPT_VERSION
    contract_version: str = CONTRACT_VERSION
    output_repair_policy: str = "transport_only"
    semantic_failure_policy: str = "reject"
