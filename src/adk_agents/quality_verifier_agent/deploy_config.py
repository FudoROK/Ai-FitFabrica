"""Deployment and runtime configuration for the FitFabrica quality verifier agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityVerifierAgentDeployConfig:
    """Immutable deployment configuration for the quality verifier ADK runtime."""

    name: str = "quality_verifier_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica quality verifier decision agent."
