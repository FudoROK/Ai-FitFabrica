"""Typed contracts for the FitFabrica material and texture agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class MaterialTextureContract(StrictAgentContractModel):
    """Structured material and texture observations with explicit uncertainty."""

    visible_material_signals: list[str] = Field(default_factory=list)
    texture_signals: list[str] = Field(default_factory=list)
    evidence_note: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
