"""Typed contracts for the FitFabrica fashion stylist agent."""

from __future__ import annotations

from pydantic import Field

from src.domain.image_agent_contracts import AgentEvidence, StrictImageAgentModel, UncertaintyLevel


class FashionStylistRequest(StrictImageAgentModel):
    """Quality-approved facts used for final practical style guidance."""

    final_image_object_key: str = Field(min_length=1)
    approved_style_facts: list[str] = Field(min_length=1)
    user_context: list[str] = Field(default_factory=list)


class FashionStylistNoteContract(StrictImageAgentModel):
    """Structured stylist note payload returned after Try-On quality and repair stages."""

    note: str = Field(min_length=1)
    outfit_tips: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW
