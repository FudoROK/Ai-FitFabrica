"""Typed contracts for the FitFabrica user profile agent."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentContractModel(BaseModel):
    """Base model that forbids undeclared fields in agent payloads."""

    model_config = ConfigDict(extra="forbid")


class UserProfileContract(StrictAgentContractModel):
    """Structured B2C style and preference summary for backend workflows."""

    style_preferences: list[str] = Field(default_factory=list)
    size_signals: list[str] = Field(default_factory=list)
    budget_preference: str = Field(min_length=1)
    fit_preferences: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
