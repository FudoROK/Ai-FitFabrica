"""Deployment and runtime configuration for the FitFabrica garment identity agent."""

from dataclasses import dataclass

from .prompt_config import CONTRACT_VERSION, PROMPT_VERSION


@dataclass(frozen=True)
class GarmentIdentityAgentDeployConfig:
    """Immutable deployment configuration for the garment identity ADK runtime."""

    name: str = "garment_identity_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica garment identity preservation agent."
    prompt_version: str = PROMPT_VERSION
    contract_version: str = CONTRACT_VERSION
    output_repair_policy: str = "transport_only"
    semantic_failure_policy: str = "reject"
