from __future__ import annotations

from src.adk_agents.primary_agent.prompt_config import (
    QUALIFIER_DESCRIPTION,
    QUALIFIER_INSTRUCTION,
    ROUTER_DESCRIPTION,
    ROUTER_INSTRUCTION,
)


def test_primary_agent_prompt_requires_runtime_envelope_v1() -> None:
    assert "`primary_runtime_envelope_v1` является runtime envelope contract." in QUALIFIER_INSTRUCTION
    assert "`backend_context` является авторитетным источником профиля клиента, памяти и истории." in QUALIFIER_INSTRUCTION
    assert "Если `backend_context`/history/session содержит известные данные (например, `last_messages` не пуст, или `rolling_summary` не пуст, или `lead_snapshot.first_name` известен), это НЕ первое знакомство с клиентом." in QUALIFIER_INSTRUCTION
    assert "Не повторять приветственный intro при продолжающемся диалоге." in QUALIFIER_INSTRUCTION
    assert "Не выдумывать имя, если оно не передано явно." in QUALIFIER_INSTRUCTION
    assert "Structured output должен соответствовать текущему контракту backend." in QUALIFIER_INSTRUCTION
    assert "reply_text must contain only the user-facing reply." in QUALIFIER_INSTRUCTION
    assert "system_payload may contain only lead_patch.first_name." in QUALIFIER_INSTRUCTION
    assert "Set lead_patch.first_name only when the user explicitly states their first name in the current message." in QUALIFIER_INSTRUCTION
    assert "If the name is not explicitly stated, return null for lead_patch.first_name." in QUALIFIER_INSTRUCTION
    assert "Do not invent extra fields." in QUALIFIER_INSTRUCTION


def test_primary_agent_prompt_treats_backend_context_as_authoritative() -> None:
    # This test is now covered by test_primary_agent_prompt_requires_runtime_envelope_v1
    pass


def test_primary_agent_prompt_forbids_repeat_intro_when_history_exists() -> None:
    # This test is now covered by test_primary_agent_prompt_requires_runtime_envelope_v1
    pass


def test_primary_agent_router_prompt_understands_runtime_envelope() -> None:
    assert "You are the routing layer." in ROUTER_INSTRUCTION
    assert "Route every normal user message to primary_agent." in ROUTER_INSTRUCTION
    assert "reply_text must be an empty string." in ROUTER_INSTRUCTION
    assert "system_payload.lead_patch.first_name must be null." in ROUTER_INSTRUCTION
    assert "Do not add any other fields." in ROUTER_INSTRUCTION
    assert "Primary agent with backend memory continuity and minimal first_name-only structured extraction." in QUALIFIER_DESCRIPTION
    assert "Routing-only skeleton that always delegates to primary_agent." in ROUTER_DESCRIPTION
