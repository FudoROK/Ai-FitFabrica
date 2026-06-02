"""Typed contracts for the FitFabrica fashion stylist agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class FashionStylistNoteContract(StrictAgentContractModel):
    """Structured stylist note payload returned after Try-On quality and repair stages."""

    note: str = Field(min_length=1)
    outfit_tips: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
