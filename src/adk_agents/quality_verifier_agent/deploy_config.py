"""Deployment and runtime configuration for the FitFabrica quality verifier agent."""

from dataclasses import dataclass

from .prompt_config import CONTRACT_VERSION, PROMPT_VERSION


@dataclass(frozen=True)
class QualityVerifierAgentDeployConfig:
    """Immutable deployment configuration for the quality verifier ADK runtime."""

    name: str = "quality_verifier_agent"
    model: str = "gemini-2.5-flash"
    description: str = "FitFabrica quality verifier decision agent."
    prompt_version: str = PROMPT_VERSION
    contract_version: str = CONTRACT_VERSION
    output_repair_policy: str = "transport_only"
    semantic_failure_policy: str = "reject"
