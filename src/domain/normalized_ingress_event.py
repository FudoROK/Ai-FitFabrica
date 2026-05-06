"""Canonical normalized ingress contract for channel adapters and ingress policies."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NormalizedIngressEvent(BaseModel):
    """Production-grade normalized ingress event contract used across ingress layers."""

    model_config = ConfigDict(extra="forbid")

    channel: str = Field(min_length=1, max_length=32)
    source_identity: str = Field(min_length=1, max_length=256)
    conversation_identity: str = Field(min_length=1, max_length=256)
    event_identity: str | int
    external_user_id: str | int | None = None
    content_type: Literal["text", "voice", "photo", "document"] = "text"
    text: str | None = Field(default=None, max_length=4096)
    timestamp: str | None = Field(default=None, max_length=64)
    username: str | None = Field(default=None, max_length=64)
    media: dict[str, object] | None = None



def build_ingress_rate_key(event: NormalizedIngressEvent) -> str:
    """Build canonical ingress anti-flood key from contract-level required fields only."""

    return f"{event.channel.strip().lower()}:{event.source_identity.strip()}"
