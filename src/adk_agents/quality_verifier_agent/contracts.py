"""Typed contracts for the FitFabrica quality verifier agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class QualityVerifierDecisionContract(StrictAgentContractModel):
    """Structured decision returned from the quality-verifier reasoning layer."""

    verdict: Literal["pass", "repair_recommended", "reject"]
    summary: str = Field(min_length=1)
    blocking_issues: list[str] = Field(default_factory=list)
    repair_targets: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
