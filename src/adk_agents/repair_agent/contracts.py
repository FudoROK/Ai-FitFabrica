"""Typed contracts for the FitFabrica repair agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class RepairInstructionContract(StrictAgentContractModel):
    """Structured local-fix instructions for backend-owned image editing paths."""

    repair_scope: str = Field(min_length=1)
    target_issues: list[str] = Field(default_factory=list)
    editing_instructions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
