from __future__ import annotations

from src.domain.channel_identity import build_channel_identity


def test_build_channel_identity_from_normalized_payload():
    identity = build_channel_identity(
        {
            "channel": "whatsapp",
            "source_identity": "wa-user-42",
            "external_user_id": "wa-user-42",
            "conversation_identity": "wa-chat-99",
        }
    )

    assert identity.channel == "whatsapp"
    assert identity.source_identity == "wa-user-42"
    assert identity.external_user_id == "wa-user-42"
    assert identity.conversation_identity == "wa-chat-99"
    assert identity.crm_identity_key == "whatsapp:wa-user-42"
    assert identity.ingress_source("webhook") == "whatsapp-webhook"


def test_build_channel_identity_keeps_legacy_message_payloads_working():
    identity = build_channel_identity(
        {
            "channel": "telegram",
            "chat_id": 123,
            "external_user_id": 456,
        }
    )

    assert identity.channel == "telegram"
    assert identity.source_identity == "456"
    assert identity.external_user_id == "456"
    assert identity.conversation_identity == "123"
