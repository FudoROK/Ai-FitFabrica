from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class EventProcessingStartResult:
    decision: Literal["started", "reclaimed", "already_processing", "already_completed"]
    status: str
    should_process: bool
    attempt_count: int
    owner_token: str | None = None
