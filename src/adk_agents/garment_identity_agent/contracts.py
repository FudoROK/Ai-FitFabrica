"""Typed contracts for the FitFabrica garment identity agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class GarmentIdentityContract(StrictAgentContractModel):
    """Structured garment facts that the backend must preserve or compare."""

    garment_type: str = Field(min_length=1)
    dominant_color: str = Field(min_length=1)
    silhouette_summary: str = Field(min_length=1)
    preserved_details: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
