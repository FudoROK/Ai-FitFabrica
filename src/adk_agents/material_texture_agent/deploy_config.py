"""Deployment and runtime configuration for the FitFabrica material and texture agent."""

from dataclasses import dataclass

from .prompt_config import CONTRACT_VERSION, PROMPT_VERSION


@dataclass(frozen=True)
class MaterialTextureAgentDeployConfig:
    """Immutable deployment configuration for the material and texture ADK runtime."""

    name: str = "material_texture_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica material and texture estimation agent."
    prompt_version: str = PROMPT_VERSION
    contract_version: str = CONTRACT_VERSION
    output_repair_policy: str = "transport_only"
    semantic_failure_policy: str = "reject"
