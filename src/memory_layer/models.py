from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActiveWindowRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lead_id: str
    timezone: str
    local_day_key: str
    window_status: Literal["open", "closing", "closed"] = "open"
    opened_at: datetime
    last_activity_at: datetime
    grace_until: Optional[datetime] = None
    last_user_message_at: Optional[datetime] = None
    last_assistant_message_at: Optional[datetime] = None
    first_message_id: Optional[str] = None
    last_message_id: Optional[str] = None
    last_assistant_message_id: Optional[str] = None
    message_count: int = 0
    updated_at: datetime
    open_topics: list[str] = Field(default_factory=list)
    local_context_text: Optional[str] = None


class ConversationStateRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    lead_id: str
    current_stage: Optional[str] = None
    pending_question: Optional[str] = None
    open_questions: list[str] = Field(default_factory=list)
    answered_topics: list[str] = Field(default_factory=list)
    followup_status: Optional[str] = None
    last_agent_role: Optional[str] = None
    response_mode: Optional[str] = None
    next_expected_move: Optional[str] = None
    state_version: int = 1
    updated_at: datetime


class MemoryMessageRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    text: str
    ts: Optional[str] = None


class MemoryReadBundle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rolling_summary: Optional[str] = None
    daily_summary: Optional[str] = None
    messages: list[MemoryMessageRecord] = Field(default_factory=list)
    active_window: Optional[ActiveWindowRecord] = None
    conversation_state: Optional[ConversationStateRecord] = None
