"""Telegram update normalization helpers."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.domain.normalized_ingress_event import NormalizedIngressEvent
from src.entrypoints.payloads import TelegramWebhookRequest

logger = logging.getLogger(__name__)


def _normalize_timestamp(raw_ts: Any) -> str:
    if isinstance(raw_ts, (int, float)):
        dt = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
    elif isinstance(raw_ts, str):
        try:
            dt = datetime.fromisoformat(raw_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def normalize_telegram_update(update: TelegramWebhookRequest) -> NormalizedIngressEvent:
    message = update.message or update.edited_message
    if message is None:
        raise ValueError("Unsupported update payload")

    content_type = "text"
    text = message.text
    media_meta: dict[str, Any] | None = None

    if message.voice is not None:
        content_type = "voice"
        text = message.caption or "[voice]"
        media_meta = {"file_id": message.voice.file_id, "duration": message.voice.duration, "mime_type": message.voice.mime_type, "file_size": message.voice.file_size}
    elif message.photo is not None:
        content_type = "photo"
        text = message.caption or "[photo]"
        media_meta = {"sizes": [{"file_id": item.file_id} for item in message.photo]}
    elif message.document is not None:
        content_type = "document"
        text = message.caption or message.document.file_name or "[document]"
        media_meta = {"file_id": message.document.file_id, "file_name": message.document.file_name, "mime_type": message.document.mime_type, "file_size": message.document.file_size}

    return NormalizedIngressEvent(
        channel="telegram",
        source_identity=str(message.from_user.id),
        external_user_id=str(message.from_user.id),
        conversation_identity=str(message.chat.id),
        text=text,
        timestamp=_normalize_timestamp(message.date),
        event_identity=update.update_id,
        content_type=content_type,
        media=media_meta,
    )
