from __future__ import annotations

import logging

import pytest

from src.domain.models import ChatSession, Lead
from src.domain.agent_output.agent_semantic_payload_validator import SemanticValidationOutcome
from src.use_cases.dialog.handle_inbound_message_use_case import HandleInboundMessageUseCase
from src.use_cases.lead.process_lead_workflow_output_use_case import ProcessWorkflowOutputUseCase


class _IngestLeadPatch:
    def __init__(self) -> None:
        self.called = 0

    async def execute(self, **_kwargs) -> bool:
        self.called += 1
        return True


@pytest.mark.asyncio
async def test_side_effects_blocked_and_telemetry_emitted_on_semantic_reject(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "memory_patch": {"important_facts_add": ["City: Berlin"]},
            "lead_patch": {},
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_REJECT_SOFT
    assert result.side_effects_applied is False
    assert ingest.called == 0
    assert "semantic_validation_started" in caplog.text
    assert "semantic_contract_violation" in caplog.text
    assert "side_effects_blocked_by_semantic_gate" in caplog.text


@pytest.mark.asyncio
async def test_side_effects_apply_on_semantic_ok() -> None:
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "lead_patch": {"city": "Berlin", "country": "Germany"},
            "memory_patch": {"important_facts_add": ["Interested in onboarding"]},
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_OK
    assert result.side_effects_applied is True
    assert ingest.called == 1


@pytest.mark.asyncio
async def test_valid_production_like_payload_with_canonical_duplication_passes() -> None:
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "lead_patch": {"city": "Berlin", "country": "Germany"},
            "memory_patch": {
                "important_facts_add": [
                    "City: Berlin",
                    "Country: Germany",
                    "Interested in onboarding",
                ]
            },
            "routing_decision": {"selected_agent": "AI_Solution_Primary_Agent"},
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_OK
    assert result.side_effects_applied is True
    assert ingest.called == 1


@pytest.mark.asyncio
async def test_canonical_substitution_still_blocked_when_only_in_memory() -> None:
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "lead_patch": {},
            "memory_patch": {"important_facts_add": ["City: Berlin", "Country: Germany"]},
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_REJECT_SOFT
    assert "canonical_location_in_memory" in result.semantic_result.violation_codes
    assert result.side_effects_applied is False
    assert ingest.called == 0


@pytest.mark.asyncio
async def test_canonical_profile_substitution_is_blocked() -> None:
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "lead_patch": {},
            "memory_patch": {
                "important_facts_add": ["lead_profile full name: Alice Doe", "budget: 15k"]
            },
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_REJECT_SOFT
    assert "canonical_profile_slot_misuse" in result.semantic_result.violation_codes
    assert result.side_effects_applied is False
    assert ingest.called == 0


@pytest.mark.asyncio
async def test_timezone_misuse_stays_blocking() -> None:
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "lead_patch": {"timezone": "Europe/Berlin", "city": None, "country": None},
            "memory_patch": {"important_facts_add": ["Timezone: Europe/Berlin"]},
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_REJECT_SOFT
    assert "timezone_without_backend_resolution_path" in result.semantic_result.violation_codes
    assert result.side_effects_applied is False
    assert ingest.called == 0


@pytest.mark.asyncio
async def test_unexpected_agent_is_non_blocking_observation() -> None:
    ingest = _IngestLeadPatch()
    use_case = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=ingest,
    )

    result = await use_case.execute(
        system_payload={
            "lead_patch": {"city": "Berlin", "country": "Germany"},
            "routing_decision": {"selected_agent": "SomeNewAgent"},
        },
        lead=Lead(lead_id="lead-1"),
        external_user_id="u-1",
    )

    assert result.semantic_result.outcome == SemanticValidationOutcome.SEMANTIC_OK
    assert "routing_decision_unexpected_agent" in result.semantic_result.observation_codes
    assert result.side_effects_applied is True
    assert ingest.called == 1


class _SendReply:
    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, **_kwargs) -> None:
        self.calls += 1


class _GenerateReply:
    async def execute(self, **_kwargs):
        return type("R", (), {"ok": True, "error": {}})(), "reply-ok", {
            "memory_patch": {"important_facts_add": ["Country: Germany"]},
            "lead_patch": {},
        }, {}


class _NoopAsync:
    async def execute(self, **_kwargs):
        return None


@pytest.mark.asyncio
async def test_reply_survives_semantic_reject_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    send_reply = _SendReply()
    workflow = ProcessWorkflowOutputUseCase(
        ingest_lead_patch_use_case=_IngestLeadPatch(),
    )
    use_case = HandleInboundMessageUseCase(
        leads_repo=object(),
        llm_service=type("S", (), {"provider": type("P", (), {"provider_name": "fake"})()})(),
        build_context=_async_context,
        generate_reply_use_case=_GenerateReply(),
        persist_conversation_use_case=_NoopAsync(),
        send_reply_use_case=send_reply,
        process_lead_workflow_output_use_case=workflow,
    )

    result = await use_case.execute(
        message={"channel": "telegram", "chat_id": "1", "external_user_id": "1", "text": "hi"},
        lead=Lead(lead_id="lead-1"),
        session=ChatSession(id="telegram:1", channel="telegram", chat_id="1", external_user_id="1", lead_id="lead-1"),
    )

    assert result.reply_text == "reply-ok"
    assert send_reply.calls == 1
    assert "reply_sent_with_semantic_reject" in caplog.text


async def _async_context(**_kwargs):
    return {}
