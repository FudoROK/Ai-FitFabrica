"""Deployment and runtime configuration for the FitFabrica Try-On agent."""

from dataclasses import dataclass

from .prompt_config import CONTRACT_VERSION, PROMPT_VERSION


@dataclass(frozen=True)
class TryOnAgentDeployConfig:
    """Immutable deployment configuration for the Try-On instruction ADK runtime."""

    name: str = "try_on_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica Try-On instruction agent."
    prompt_version: str = PROMPT_VERSION
    contract_version: str = CONTRACT_VERSION
    output_repair_policy: str = "transport_only"
    semantic_failure_policy: str = "reject"
