"""Deployment and runtime configuration for the FitFabrica user profile agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfileAgentDeployConfig:
    """Immutable deployment configuration for the user profile ADK runtime."""

    name: str = "user_profile_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica B2C user profile agent."
