"""Canonical channel identity helpers for ingress, CRM and messaging flows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _normalize_identity_part(value: object) -> str:
    return str(value or "").strip()


def _first_non_empty(*values: object) -> str:
    for value in values:
        normalized = _normalize_identity_part(value)
        if normalized:
            return normalized
    return ""


def _normalize_channel(value: object) -> str:
    normalized = _normalize_identity_part(value).lower()
    return normalized or "telegram"


@dataclass(frozen=True)
class ChannelIdentity:
    channel: str
    source_identity: str
    conversation_identity: str
    external_user_id: str

    @property
    def lead_id(self) -> str:
        return f"{self.channel}:{self.external_user_id}"

    @property
    def crm_identity_key(self) -> str:
        return f"{self.channel}:{self.external_user_id}"

    def processing_step_key(self, action: str) -> str:
        normalized_action = _normalize_identity_part(action).lower().replace("-", "_").replace(" ", "_")
        return f"{self.channel}_{normalized_action}"

    def ingress_source(self, source_kind: str = "webhook") -> str:
        normalized_kind = _normalize_identity_part(source_kind).lower().replace("_", "-")
        return f"{self.channel}-{normalized_kind}"


def build_channel_identity(payload: Mapping[str, Any]) -> ChannelIdentity:
    """Build a canonical identity object from normalized ingress or legacy message payloads."""

    channel = _normalize_channel(payload.get("channel"))
    source_identity = _first_non_empty(
        payload.get("source_identity"),
        payload.get("external_user_id"),
        payload.get("chat_id"),
    )
    external_user_id = _first_non_empty(
        payload.get("external_user_id"),
        payload.get("source_identity"),
        payload.get("chat_id"),
    )
    conversation_identity = _first_non_empty(
        payload.get("conversation_identity"),
        payload.get("chat_id"),
        payload.get("external_user_id"),
        payload.get("source_identity"),
    )

    if not source_identity:
        raise ValueError("source_identity is required")
    if not external_user_id:
        raise ValueError("external_user_id is required")
    if not conversation_identity:
        raise ValueError("conversation_identity is required")

    return ChannelIdentity(
        channel=channel,
        source_identity=source_identity,
        external_user_id=external_user_id,
        conversation_identity=conversation_identity,
    )
