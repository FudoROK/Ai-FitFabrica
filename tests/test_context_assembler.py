from __future__ import annotations

from src.services.context.context_assembler import assemble_core_context_payload
from src.services.context.context_projection import ContextProjection


def test_context_assembler_builds_payload_from_normalized_projection():
    projection = ContextProjection(
        identity={"channel": "telegram", "external_user_id": "42", "chat_id": "100", "lead_id": "telegram:42"},
        lead_snapshot={"stage": "warm"},
        memory={
            "rolling_summary": "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.",
            "daily_summary": "daily",
            "messages": [{"role": "user", "text": "hello", "ts": "2026-01-01T00:00:00+00:00"}],
            # raw storage-like noise that assembler must ignore
            "raw_message": {"sender_type": "legacy"},
        },
    )

    payload = assemble_core_context_payload(projection)

    assert payload == {
        "identity": {"channel": "telegram", "external_user_id": "42", "chat_id": "100", "lead_id": "telegram:42"},
        "lead_snapshot": {"stage": "warm"},
        "memory": {
            "rolling_summary": "Клиент подтвердил интерес, уточнил бюджет и согласовал следующий созвон на этой неделе.",
            "daily_summary": "daily",
            "last_messages": [{"role": "user", "text": "hello", "ts": "2026-01-01T00:00:00+00:00"}],
        },
    }
