"""Typed contracts for the FitFabrica Try-On agent."""

from __future__ import annotations

from pydantic import Field

from src.domain.image_agent_contracts import AgentEvidence, StrictImageAgentModel, UncertaintyLevel


class TryOnInstructionRequest(StrictImageAgentModel):
    """Approved analysis bundle used to create generation instructions."""

    human_analysis: dict[str, object] = Field(min_length=1)
    garment_analysis: dict[str, object] = Field(min_length=1)
    garment_slot_analyses: list[dict[str, object]] = Field(default_factory=list)
    material_analysis: dict[str, object] = Field(min_length=1)
    user_options: dict[str, object] = Field(default_factory=dict)


class TryOnOutfitSlotInstruction(StrictImageAgentModel):
    """Generation constraints for one garment slot."""

    slot_role: str = Field(min_length=1)
    garment_type: str = Field(min_length=1)
    focus_points: list[str] = Field(default_factory=list)
    generation_exclusions: list[str] = Field(default_factory=list)


class TryOnInstructionContract(StrictImageAgentModel):
    """Structured generation instructions consumed by the backend Try-On workflow."""

    instruction_summary: str = Field(min_length=1)
    preserve_face: bool = True
    preserve_body_shape: bool = True
    preserve_pose: bool = True
    garment_focus_points: list[str] = Field(default_factory=list)
    outfit_slot_focus_points: list[TryOnOutfitSlotInstruction] = Field(default_factory=list)
    styling_focus_points: list[str] = Field(default_factory=list)
    generation_exclusions: list[str] = Field(default_factory=list)
    expected_framing: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW
