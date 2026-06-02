"""Deployment and runtime configuration for the FitFabrica garment identity agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GarmentIdentityAgentDeployConfig:
    """Immutable deployment configuration for the garment identity ADK runtime."""

    name: str = "garment_identity_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica garment identity preservation agent."
