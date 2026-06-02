from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

TaskName = Literal[
    "dialog_reply_task",
    "profile_extract_task",
    "memory_daily_sync_task",
    "memory_rolling_sync_task",
]


@dataclass
class LLMMeta:
    trace_id: Optional[str] = None
    message_id: Optional[str] = None
    lead_id: Optional[str] = None
    channel: Optional[str] = None
    delivery_id: Optional[str] = None


@dataclass
class LLMRequest:
    task: TaskName
    payload: dict[str, Any]
    meta: LLMMeta = field(default_factory=LLMMeta)


@dataclass
class LLMResult:
    task: TaskName
    ok: bool
    data: dict[str, Any] | None = None
    provider_metadata: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
