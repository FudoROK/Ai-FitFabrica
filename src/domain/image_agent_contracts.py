"""Shared strict contracts for backend-controlled image workflow agents."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_FORBIDDEN_SAFETY_REQUESTS = (
    "identify the person",
    "identify person",
    "ethnicity",
    "health condition",
    "medical condition",
    "protected attribute",
)


class StrictImageAgentModel(BaseModel):
    """Base model that forbids undeclared image-agent fields."""

    model_config = ConfigDict(extra="forbid")


class UncertaintyLevel(str, Enum):
    """Explicit uncertainty level for evidence-driven image analysis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AgentEvidence(StrictImageAgentModel):
    """One evidence-backed observation used by an image workflow agent."""

    source_type: Literal["artifact", "backend_fact", "prior_agent_output", "generated_result", "trusted_product_data"]
    source_ref: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class SafeBackendFactsModel(StrictImageAgentModel):
    """Strict request base that rejects prohibited sensitive-analysis requests."""

    backend_facts: list[str] = Field(default_factory=list)

    @field_validator("backend_facts")
    @classmethod
    def reject_prohibited_sensitive_analysis(cls, values: list[str]) -> list[str]:
        """Reject backend facts that attempt to authorize prohibited inference."""

        for value in values:
            normalized = value.strip().lower()
            if any(term in normalized for term in _FORBIDDEN_SAFETY_REQUESTS):
                raise ValueError("prohibited sensitive analysis request")
        return values

