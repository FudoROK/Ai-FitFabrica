"""Typed contracts for the FitFabrica human identity agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class HumanIdentityPreservationTarget(StrictAgentContractModel):
    """One human attribute that the backend must preserve during image workflows."""

    attribute_name: str = Field(min_length=1)
    preservation_reason: str = Field(min_length=1)


class HumanIdentityContract(StrictAgentContractModel):
    """Structured human-identity facts required by backend-owned Try-On orchestration."""

    face_visibility: str = Field(min_length=1)
    pose_summary: str = Field(min_length=1)
    body_region_visibility: list[str] = Field(default_factory=list)
    preservation_targets: list[HumanIdentityPreservationTarget] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
