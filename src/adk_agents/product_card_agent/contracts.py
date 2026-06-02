"""Typed contracts for the FitFabrica product card agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class ProductCardContentContract(StrictAgentContractModel):
    """Structured product-card content package for backend-owned B2B workflows."""

    title: str = Field(min_length=1)
    short_description: str = Field(min_length=1)
    key_attributes: list[str] = Field(default_factory=list)
    merchandising_notes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
