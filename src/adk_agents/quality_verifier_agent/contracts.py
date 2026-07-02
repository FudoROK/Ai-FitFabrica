"""Typed contracts for the FitFabrica quality verifier agent."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from src.domain.image_agent_contracts import AgentEvidence, StrictImageAgentModel, UncertaintyLevel


class QualityVerifierRequest(StrictImageAgentModel):
    """Backend-approved source and result references for quality verification."""

    human_photo_object_key: str = Field(min_length=1)
    garment_photo_object_key: str = Field(min_length=1)
    generated_image_object_key: str = Field(min_length=1)
    approved_constraints: list[str] = Field(default_factory=list)


class QualityVerdict(str, Enum):
    """Verifier recommendation consumed by backend decision policy."""

    PASS = "pass"
    REPAIR_RECOMMENDED = "repair_recommended"
    REJECT = "reject"


class QualityDefect(StrictImageAgentModel):
    """One evidence-backed defect detected in a generated result."""

    defect_type: Literal[
        "face",
        "body",
        "pose",
        "garment",
        "color",
        "texture",
        "hands",
        "neck",
        "waist",
        "background",
        "realism",
        "wear_control",
        "other",
    ]
    region: str = Field(min_length=1)
    severity: Literal["minor", "major", "blocking"]
    evidence: str = Field(min_length=1)
    repairable: bool
    confidence: float = Field(ge=0.0, le=1.0)


class QualityCategoryScore(StrictImageAgentModel):
    """One category score used by backend quality policy."""

    category: Literal[
        "face",
        "body_pose",
        "garment_details",
        "color",
        "texture",
        "anatomy",
        "background",
        "realism",
        "wear_control_match",
    ]
    score: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(min_length=1)


class QualityVerifierDecisionContract(StrictImageAgentModel):
    """Structured decision returned from the quality-verifier reasoning layer."""

    verdict: QualityVerdict
    summary: str = Field(min_length=1)
    blocking_issues: list[str] = Field(default_factory=list)
    repair_targets: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    defects: list[QualityDefect] = Field(default_factory=list)
    category_scores: list[QualityCategoryScore] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW

    @model_validator(mode="after")
    def validate_verdict_against_defects(self) -> QualityVerifierDecisionContract:
        """Reject pass recommendations that contain blocking defects."""

        if self.verdict is QualityVerdict.PASS and any(item.severity == "blocking" for item in self.defects):
            raise ValueError("pass verdict cannot contain blocking defects")
        return self
