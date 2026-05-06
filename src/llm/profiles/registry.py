from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .memory_profile import MemoryProfile
from .reply_profile import ReplyProfile


@dataclass(frozen=True)
class ProfileRegistry:
    """Single orchestration-level profile selection point."""

    reply_profile: ReplyProfile = ReplyProfile()
    memory_profile: MemoryProfile = MemoryProfile()

    def get_profile(self, *, flow: str) -> Any:
        normalized = str(flow or "").strip().lower()
        if normalized == "primary_agent_reply_task":
            return self.reply_profile
        if normalized == "memory":
            return self.memory_profile
        raise ValueError(f"unknown_profile_flow:{normalized or 'empty'}")
