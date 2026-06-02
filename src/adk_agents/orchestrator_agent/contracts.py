"""Typed contracts for the FitFabrica orchestrator agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class OrchestratorDecisionContract(StrictAgentContractModel):
    """Structured workflow-routing decision returned to backend orchestration."""

    workflow_type: str = Field(min_length=1)
    requested_capabilities: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
