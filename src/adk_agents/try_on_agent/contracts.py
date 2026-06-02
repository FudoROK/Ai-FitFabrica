"""Typed contracts for the FitFabrica Try-On agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class TryOnInstructionContract(StrictAgentContractModel):
    """Structured generation instructions consumed by the backend Try-On workflow."""

    instruction_summary: str = Field(min_length=1)
    preserve_face: bool = True
    preserve_body_shape: bool = True
    preserve_pose: bool = True
    garment_focus_points: list[str] = Field(default_factory=list)
    styling_focus_points: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
