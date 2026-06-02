"""Typed contracts for the FitFabrica business profile agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class BusinessProfileContract(StrictAgentContractModel):
    """Structured B2B seller profile summary for backend workflows."""

    brand_style: list[str] = Field(default_factory=list)
    target_channels: list[str] = Field(default_factory=list)
    content_rules: list[str] = Field(default_factory=list)
    pricing_positioning: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
