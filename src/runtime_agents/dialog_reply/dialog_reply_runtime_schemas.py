from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class DialogReplyRuntimeOutput(BaseModel):
    """Canonical runtime output contract for backend-owned dialog reply generation."""

    model_config = ConfigDict(extra="forbid")

    reply_text: str
    system_payload: dict[str, Any]
