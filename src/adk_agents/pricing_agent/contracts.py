"""Typed contracts for the FitFabrica pricing agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class PricingRecommendationContract(StrictAgentContractModel):
    """Structured pricing explanation for backend-owned recommendation workflows."""

    pricing_positioning: str = Field(min_length=1)
    recommended_price_band: str = Field(min_length=1)
    evidence_highlights: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
