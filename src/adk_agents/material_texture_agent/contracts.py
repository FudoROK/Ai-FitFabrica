"""Typed contracts for the FitFabrica material and texture agent."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from src.domain.image_agent_contracts import AgentEvidence, SafeBackendFactsModel, StrictImageAgentModel, UncertaintyLevel


class MaterialTextureRequest(SafeBackendFactsModel):
    """Backend-approved request for visible material and texture analysis."""

    garment_photo_object_key: str = Field(min_length=1)
    trusted_material_facts: list[str] = Field(default_factory=list)


class MaterialObservation(StrictImageAgentModel):
    """One visible material behavior observation."""

    signal_type: Literal["weave", "knit", "finish", "gloss", "transparency", "stiffness", "drape", "texture"]
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class MaterialTextureContract(StrictImageAgentModel):
    """Structured material and texture observations with explicit uncertainty."""

    visible_material_signals: list[str] = Field(default_factory=list)
    texture_signals: list[str] = Field(default_factory=list)
    evidence_note: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    composition_status: Literal["unknown", "trusted_fact_provided"] = "unknown"
    observations: list[MaterialObservation] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.MEDIUM
    alternative_interpretations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_composition_evidence(self) -> MaterialTextureContract:
        """Require trusted product evidence before confirming material composition."""

        if self.composition_status == "trusted_fact_provided" and not any(
            item.source_type == "trusted_product_data" for item in self.evidence
        ):
            raise ValueError("trusted composition requires trusted_product_data evidence")
        return self
