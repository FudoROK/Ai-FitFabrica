from __future__ import annotations

"""Canonical runtime agent output contracts used by LLM/runtime layers."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LeadPatch(StrictBaseModel):
    first_name: Optional[str] = Field(
        default=None,
        description="Client first name only when it is explicitly stated in the conversation.",
    )


class SystemPayload(StrictBaseModel):
    lead_patch: Optional[LeadPatch] = Field(
        default=None,
        description="Minimal structured payload for the backend. Only explicit client name extraction is allowed.",
    )


class AgentOutput(StrictBaseModel):
    reply_text: str = Field(
        ...,
        description="Final user-visible reply that will be sent to the client.",
    )
    system_payload: SystemPayload = Field(
        ...,
        description="Structured internal payload extracted from the conversation for backend orchestration.",
    )
