"""Domain models describing chat sessions and leads."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRole(str, Enum):
    """Roles used in chat messages."""

    USER = "user"
    ASSISTANT = "assistant"


class ChatEventType(str, Enum):
    """Types of chat events stored in history or analytics."""

    USER_MESSAGE = "user_message"
    BOT_MESSAGE = "bot_message"
    SYSTEM = "system"




class MessageEntry(BaseModel):
    """Single message entry in the rolling chat history."""

    role: Literal["user", "assistant"]
    text: str
    ts: Optional[datetime] = None


class ChatSession(BaseModel):
    """Represents a chat session stored in Firestore."""

    # Pydantic будет игнорировать лишние поля из Firestore, если они появятся
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    channel: Optional[Literal["telegram", "whatsapp", "instagram"]] = None

    # Адрес чата в канале (для Telegram — chat_id)
    chat_id: Optional[str] = None

    # Внешний идентификатор пользователя (channel_user_id / phone / username и т.п.)
    external_user_id: Optional[str] = None

    lead_id: Optional[str] = None
    last_messages: List[MessageEntry] = Field(default_factory=list)
    current_stage: Optional[str] = None
    last_user_message_at: Optional[datetime] = None
    last_bot_message_at: Optional[datetime] = None
    language: Optional[str] = None
    detected_language: Optional[str] = None
    name_attempts: int = 0
    business_attempts: int = 0
    name_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_update_id: Optional[int] = None
    message_count: int = 0
    vertex_session_id: Optional[str] = None

    def add_message(self, role: Literal["user", "assistant"], text: str, ts: Optional[datetime] = None) -> None:
        """Append a message to history keeping only the recent 30 entries."""

        entry = MessageEntry(role=role, text=text, ts=ts or datetime.now(timezone.utc))
        history = list(self.last_messages)
        history.append(entry)
        if len(history) > 30:
            history = history[-30:]
        self.last_messages = history
        self.message_count = len(self.last_messages)


class Lead(BaseModel):
    """Represents a lead entity with the simplified schema."""

    model_config = ConfigDict(extra="ignore")

    # Identification
    lead_id: Optional[str] = None
    timestamp_created: Optional[datetime] = None
    source: Optional[str] = None
    primary_channel: Optional[str] = None
    channel_user_id: Optional[str] = None
    username_or_contact: Optional[str] = None
    contact_channel: Optional[str] = None
    contact_details: Optional[str] = None
    has_contact: bool = False

    # Profile
    first_name: Optional[str] = None
    gender: Optional[Literal["male", "female", "unknown"]] = None
    city: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    timezone_source: Optional[str] = None
    timezone_confidence: Optional[float] = None
    timezone_updated_at: Optional[datetime] = None

    # Business
    business_type: Optional[str] = None             # custom_<slug>
    business_slug: Optional[str] = None             # slug without prefix
    business_description: Optional[str] = None      # human text from client/GPT
    business_source: Optional[str] = None           # "intro", "gpt_profile", "trigger", "fallback"

    has_pains: bool = False
    has_needs: bool = False

    # Additional fields
    has_table_or_crm: Optional[Union[str, bool]] = None
    needs_multichannel: Optional[Union[str, bool]] = None

    # Intro flow flags
    has_name: bool = False
    has_business: bool = False
    stage: Optional[str] = None
    status: Optional[str] = None
    niche_key: Optional[str] = None

    # Lead status
    recommended_package: Optional[str] = None
    last_contact_at: Optional[datetime] = None
    next_followup_at: Optional[datetime] = None

    # Notes
    summary_short: Optional[str] = None
    notes: Optional[str] = None
    lead_profile: Optional[dict[str, Any]] = None
    rolling_summary: Optional[str] = None
    rolling_summary_updated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    crm_contact_ref: Optional[str] = None
    crm_provider: Optional[str] = None
    person_id: Optional[str] = None

    def identity_section(self) -> dict[str, Optional[str]]:
        return {
            "lead_id": self.lead_id,
            "channel_user_id": self.channel_user_id,
            "primary_channel": self.primary_channel,
            "username_or_contact": self.username_or_contact,
            "contact_channel": self.contact_channel,
            "contact_details": self.contact_details,
            "person_id": self.person_id,
        }

    def business_profile_section(self) -> dict[str, Optional[str]]:
        lead_profile = self.lead_profile if isinstance(self.lead_profile, dict) else {}
        needs = lead_profile.get("needs") if isinstance(lead_profile.get("needs"), list) else None
        pain_points = lead_profile.get("pain_points") if isinstance(lead_profile.get("pain_points"), list) else None
        return {
            "first_name": self.first_name,
            "business_type": self.business_type,
            "business_description": self.business_description,
            "needs": ", ".join(str(item) for item in needs) if needs else None,
            "pain_points": ", ".join(str(item) for item in pain_points) if pain_points else None,
            "recommended_package": self.recommended_package,
            "city": self.city,
            "country": self.country,
            "timezone": self.timezone,
            "timezone_source": self.timezone_source,
            "timezone_confidence": self.timezone_confidence,
            "timezone_updated_at": self.timezone_updated_at,
        }

    def conversation_state_section(self) -> dict[str, Optional[object]]:
        return {
            "stage": self.stage,
            "status": self.status,
            "has_name": self.has_name,
            "has_business": self.has_business,
            "has_pains": self.has_pains,
            "has_needs": self.has_needs,
            "last_contact_at": self.last_contact_at,
            "last_activity_at": self.last_activity_at,
        }

    def memory_section(self) -> dict[str, Optional[object]]:
        return {
            "lead_profile": self.lead_profile,
            "summary_short": self.summary_short,
            "notes": self.notes,
            "rolling_summary": self.rolling_summary,
            "rolling_summary_updated_at": self.rolling_summary_updated_at,
        }

    def integration_refs_section(self) -> dict[str, Optional[str]]:
        return {
            "crm_contact_ref": self.crm_contact_ref,
            "crm_provider": self.crm_provider,
            "person_id": self.person_id,
        }

    def canonical_sections(self) -> dict[str, dict[str, Optional[object]]]:
        return {
            "identity": self.identity_section(),
            "business_profile": self.business_profile_section(),
            "conversation_state": self.conversation_state_section(),
            "memory": self.memory_section(),
            "integration_refs": self.integration_refs_section(),
        }
