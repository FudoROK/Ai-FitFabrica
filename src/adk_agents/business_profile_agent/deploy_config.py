"""Deployment and runtime configuration for the FitFabrica business profile agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessProfileAgentDeployConfig:
    """Immutable deployment configuration for the business profile ADK runtime."""

    name: str = "business_profile_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica B2B business profile agent."
