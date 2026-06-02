"""Typed contracts for the FitFabrica trend agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class TrendSignalContract(StrictAgentContractModel):
    """Structured trend interpretation that the backend can surface safely."""

    trend_summary: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
