"""Typed contracts for the FitFabrica repair agent."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from src.domain.image_agent_contracts import AgentEvidence, StrictImageAgentModel, UncertaintyLevel


class RepairDefectInput(StrictImageAgentModel):
    """One backend-approved defect that may be considered for local repair."""

    defect_type: str = Field(min_length=1)
    region: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class RepairAgentRequest(StrictImageAgentModel):
    """Backend-approved request for a narrow local repair plan."""

    generated_image_object_key: str = Field(min_length=1)
    approved_defects: list[RepairDefectInput] = Field(min_length=1)
    immutable_regions: list[str] = Field(default_factory=list)


class RepairRegionInstruction(StrictImageAgentModel):
    """One ordered local image-editing instruction."""

    region: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    preserve: list[str] = Field(default_factory=list)


class RepairInstructionContract(StrictImageAgentModel):
    """Structured local-fix instructions for backend-owned image editing paths."""

    repair_scope: Literal["local", "unsafe"]
    target_issues: list[str] = Field(default_factory=list)
    editing_instructions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    region_instructions: list[RepairRegionInstruction] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW

    @model_validator(mode="after")
    def validate_local_repair_plan(self) -> RepairInstructionContract:
        """Require scoped region instructions for every local repair plan."""

        if self.repair_scope == "local" and not self.region_instructions:
            raise ValueError("local repair requires region instructions")
        return self
