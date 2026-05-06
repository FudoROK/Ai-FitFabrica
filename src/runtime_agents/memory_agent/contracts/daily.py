from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import StrictContractModel


class ActiveWindowUpdate(StrictContractModel):
    open_topics: list[str] = Field(default_factory=list)
    local_context_text: str | None = None
    memory_relevance_flags: list[str] = Field(default_factory=list)


class DailySummaryPayload(StrictContractModel):
    summary_text: str
    open_questions: list[str] = Field(default_factory=list)
    carry_forward_notes: list[str] = Field(default_factory=list)
    learned_facts: list[str] = Field(default_factory=list)
    changed_facts: list[str] = Field(default_factory=list)
    memory_relevance_flags: list[str] = Field(default_factory=list)


class ConversationStateUpdate(StrictContractModel):
    current_stage: str | None = None
    pending_question: str | None = None
    open_questions: list[str] = Field(default_factory=list)
    answered_topics: list[str] = Field(default_factory=list)
    followup_status: str | None = None
    last_agent_role: str | None = None
    response_mode: str | None = None
    next_expected_move: str | None = None


class DailyMemoryInputContract(StrictContractModel):
    lead_snapshot: dict[str, Any] = Field(default_factory=dict)
    closed_active_window: dict[str, Any] = Field(default_factory=dict)
    conversation_state: dict[str, Any] = Field(default_factory=dict)
    timezone: str | None = None


class DailyMemoryContract(StrictContractModel):
    active_window_update: ActiveWindowUpdate | None = None
    daily_summary: DailySummaryPayload
    conversation_state_update: ConversationStateUpdate | None = None


__all__ = [
    "ActiveWindowUpdate",
    "DailySummaryPayload",
    "ConversationStateUpdate",
    "DailyMemoryInputContract",
    "DailyMemoryContract",
]
