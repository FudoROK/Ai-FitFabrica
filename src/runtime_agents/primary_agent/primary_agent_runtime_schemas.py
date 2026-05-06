from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class MainAgentRuntimeOutput(BaseModel):
    """Canonical runtime output contract for reply generation."""

    model_config = ConfigDict(extra="forbid")

    reply_text: str
    system_payload: dict[str, Any]
