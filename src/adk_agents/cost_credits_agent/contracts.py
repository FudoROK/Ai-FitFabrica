"""Typed contracts for the FitFabrica cost and credits agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class CreditChargeComponent(StrictAgentContractModel):
    """One structured component in a backend-owned credit explanation."""

    component_name: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class CostCreditsExplanationContract(StrictAgentContractModel):
    """Structured cost explanation that does not replace backend billing truth."""

    workflow_type: str = Field(min_length=1)
    charge_components: list[CreditChargeComponent] = Field(default_factory=list)
    total_credit_estimate: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
