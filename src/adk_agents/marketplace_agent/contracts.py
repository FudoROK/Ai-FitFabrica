"""Typed contracts for the FitFabrica marketplace agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class MarketplaceSearchStrategyContract(StrictAgentContractModel):
    """Structured marketplace retrieval guidance for backend-owned search workflows."""

    retrieval_intent: str = Field(min_length=1)
    comparison_axes: list[str] = Field(default_factory=list)
    source_constraints: list[str] = Field(default_factory=list)
    budget_filters: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
