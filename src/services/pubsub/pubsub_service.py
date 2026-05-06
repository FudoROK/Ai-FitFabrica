"""Pub/Sub helpers for publishing normalized chatbot messages."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Dict

from google.cloud import pubsub_v1

from src.domain.channel_identity import build_channel_identity
from src.entrypoints.payloads import PubSubNormalizedPayload
from src.settings import load_settings

logger = logging.getLogger(__name__)


@lru_cache()
def _publisher() -> pubsub_v1.PublisherClient:
    return pubsub_v1.PublisherClient()


def publish_normalized_update(
    normalized: Dict[str, object],
    *,
    topic: str | None = None,
    project_id: str | None = None,
) -> str:
    """Publish normalized update to the configured Pub/Sub topic."""

    settings = load_settings()
    validated_payload = PubSubNormalizedPayload.model_validate(normalized)
    data_bytes = json.dumps(validated_payload.model_dump(exclude_none=True), ensure_ascii=False).encode("utf-8")
    identity = build_channel_identity(validated_payload.model_dump(exclude_none=True))

    publisher = _publisher()
    topic_name = topic or settings.pubsub_topic_name
    project = project_id or settings.gcp_project_id
    topic_path = publisher.topic_path(project, topic_name)

    future = publisher.publish(topic_path, data=data_bytes, source=identity.ingress_source("webhook"))
    message_id = future.result()
    logger.info("PUBSUB_PUBLISHED", extra={"topic": topic_path, "pubsub_message_id": message_id, "status": "ok", "task": "dialog_reply"})
    return message_id
