from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..reply_task_contract import is_reply_runtime_task, normalize_reply_runtime_task
from .memory_profile import MemoryProfile
from .reply_profile import ReplyProfile


@dataclass(frozen=True)
class ProfileRegistry:
    """Single orchestration-level profile selection point."""

    reply_profile: ReplyProfile = ReplyProfile()
    memory_profile: MemoryProfile = MemoryProfile()

    def get_profile(self, *, flow: str) -> Any:
        normalized = normalize_reply_runtime_task(str(flow or "").strip().lower())
        if is_reply_runtime_task(normalized):
            return self.reply_profile
        if normalized == "memory":
            return self.memory_profile
        raise ValueError(f"unknown_profile_flow:{normalized or 'empty'}")
