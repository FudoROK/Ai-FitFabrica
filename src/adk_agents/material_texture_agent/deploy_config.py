"""Deployment and runtime configuration for the FitFabrica material and texture agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialTextureAgentDeployConfig:
    """Immutable deployment configuration for the material and texture ADK runtime."""

    name: str = "material_texture_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica material and texture estimation agent."
