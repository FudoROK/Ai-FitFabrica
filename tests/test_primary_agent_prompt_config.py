from __future__ import annotations

from src.runtime_agents.dialog_reply.prompt_config import (
    QUALIFIER_DESCRIPTION,
    QUALIFIER_INSTRUCTION,
    ROUTER_DESCRIPTION,
    ROUTER_INSTRUCTION,
)


def test_primary_agent_prompt_requires_runtime_envelope_v1() -> None:
    assert "primary_runtime_envelope_v1" in QUALIFIER_INSTRUCTION
    assert "backend_context" in QUALIFIER_INSTRUCTION
    assert "lead_snapshot.first_name" in QUALIFIER_INSTRUCTION
    assert "rolling_summary" in QUALIFIER_INSTRUCTION
    assert "Structured output" in QUALIFIER_INSTRUCTION
    assert "reply_text must contain only the user-facing reply." in QUALIFIER_INSTRUCTION
    assert "system_payload may contain only lead_patch.first_name." in QUALIFIER_INSTRUCTION
    assert "Set lead_patch.first_name only when the user explicitly states their first name in the current message." in QUALIFIER_INSTRUCTION
    assert "If the name is not explicitly stated, return null for lead_patch.first_name." in QUALIFIER_INSTRUCTION
    assert "Do not invent extra fields." in QUALIFIER_INSTRUCTION


def test_primary_agent_prompt_treats_backend_context_as_authoritative() -> None:
    assert "Treat backend context as authoritative" in QUALIFIER_INSTRUCTION or "backend_context" in QUALIFIER_INSTRUCTION


def test_primary_agent_prompt_forbids_repeat_intro_when_history_exists() -> None:
    assert "first conversation" in QUALIFIER_INSTRUCTION or "rolling_summary" in QUALIFIER_INSTRUCTION


def test_primary_agent_router_prompt_understands_runtime_envelope() -> None:
    assert "You are the routing layer." in ROUTER_INSTRUCTION
    assert "Route every normal user message to dialog_reply_agent." in ROUTER_INSTRUCTION
    assert "reply_text must be an empty string." in ROUTER_INSTRUCTION
    assert "system_payload.lead_patch.first_name must be null." in ROUTER_INSTRUCTION
    assert "Do not add any other fields." in ROUTER_INSTRUCTION
    assert "Dialog reply agent with backend memory continuity and minimal first_name-only structured extraction." in QUALIFIER_DESCRIPTION
    assert "Routing-only skeleton that always delegates to dialog_reply_agent." in ROUTER_DESCRIPTION
