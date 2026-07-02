from __future__ import annotations

import pytest

from src.adapters.agents.try_on_instruction import TryOnInstructionAgentAdapter
from src.domain.agent_runtime import AgentInvocationEnvelope, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import TryOnWearControlSelection
from src.use_cases.try_on.instruction_errors import TryOnInstructionFailure
from tests.try_on_analysis_bundle_stub import approved_analysis_bundle


class _InvocationServiceStub:
    def __init__(self, envelope: AgentInvocationEnvelope) -> None:
        self.envelope = envelope
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append((request, output_contract))
        return self.envelope


def _envelope(*, confidence: float = 0.91, output_overrides: dict[str, object] | None = None) -> AgentInvocationEnvelope:
    output: dict[str, object] = {
        "instruction_summary": "Preserve the person and apply the approved garment.",
        "preserve_face": True,
        "preserve_body_shape": True,
        "preserve_pose": True,
        "garment_focus_points": ["front closure"],
        "styling_focus_points": ["natural layering"],
        "generation_exclusions": ["body reshaping"],
        "expected_framing": "full body",
        "confidence": confidence,
        "limitations": [],
        "evidence": [
            {
                "source_type": "prior_agent_output",
                "source_ref": "garment_identity",
                "observation": "front closure must be preserved",
                "confidence": 0.9,
            }
        ],
        "uncertainty_level": "low",
    }
    if output_overrides is not None:
        output.update(output_overrides)
    return AgentInvocationEnvelope(
        invocation_id="instruction-1",
        trace_id="try_on_1",
        agent_name="try_on_agent",
        prompt_version="try_on.v1",
        contract_version="try_on.contract.v2",
        status=AgentRuntimeStatus.SUCCEEDED,
        validation_status=AgentValidationStatus.PASSED,
        output=output,
        provider="replaceable-provider",
        model="provider-model",
        latency_ms=20,
        confidence=confidence,
    )


@pytest.mark.anyio
async def test_instruction_agent_receives_only_approved_structured_analyses() -> None:
    invocation_service = _InvocationServiceStub(_envelope())
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=invocation_service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    instruction = await adapter.create(job_id="try_on_1", analysis_bundle=approved_analysis_bundle())

    request, output_contract = invocation_service.requests[0]
    assert set(request.input_payload) == {
        "human_analysis",
        "garment_analysis",
        "garment_slot_analyses",
        "material_analysis",
        "user_options",
    }
    assert request.input_payload["garment_slot_analyses"][0]["slot_role"] == "garment_photo"
    assert request.artifact_references == []
    assert output_contract.__name__ == "TryOnInstructionContract"
    assert instruction.invocation_id == "instruction-1"
    assert instruction.preserve_face is True


@pytest.mark.anyio
async def test_instruction_agent_persists_outfit_slot_focus_points() -> None:
    invocation_service = _InvocationServiceStub(
        _envelope(
            output_overrides={
                "outfit_slot_focus_points": [
                    {
                        "slot_role": "upper_garment_photo",
                        "garment_type": "shirt",
                        "focus_points": ["keep shirt hem visible"],
                        "generation_exclusions": ["do not tuck into waistband"],
                    },
                    {
                        "slot_role": "lower_garment_photo",
                        "garment_type": "jeans",
                        "focus_points": ["preserve waistband height"],
                        "generation_exclusions": [],
                    },
                ]
            }
        )
    )
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=invocation_service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    instruction = await adapter.create(job_id="try_on_1", analysis_bundle=approved_analysis_bundle())

    assert [item.slot_role for item in instruction.outfit_slot_focus_points] == [
        "upper_garment_photo",
        "lower_garment_photo",
    ]
    assert instruction.outfit_slot_focus_points[0].focus_points == ["keep shirt hem visible"]


@pytest.mark.anyio
async def test_instruction_agent_injects_backend_validated_wear_controls() -> None:
    invocation_service = _InvocationServiceStub(
        _envelope(
            output_overrides={
                "outfit_slot_focus_points": [
                    {
                        "slot_role": "garment_photo",
                        "garment_type": "coat",
                        "focus_points": ["preserve lapels"],
                        "generation_exclusions": [],
                    }
                ]
            }
        )
    )
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=invocation_service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    instruction = await adapter.create(
        job_id="try_on_1",
        analysis_bundle=approved_analysis_bundle(),
        wear_control_selections=[
            TryOnWearControlSelection(
                slot_role="garment_photo",
                garment_type="coat",
                requested_control_code="open_front",
                resolved_control_code="open_front",
                display_name="Open front",
                instruction_template="Keep the coat open without hiding the base outfit.",
                risk_level="low",
                resolved_by="user_selection",
            )
        ],
    )

    request, _output_contract = invocation_service.requests[0]
    assert request.input_payload["user_options"]["wear_control_selections"][0]["resolved_control_code"] == "open_front"
    assert instruction.outfit_slot_focus_points[0].focus_points == [
        "preserve lapels",
        "Keep the coat open without hiding the base outfit.",
    ]


@pytest.mark.anyio
async def test_instruction_agent_blocks_opposite_wear_control_instruction() -> None:
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=_InvocationServiceStub(
            _envelope(
                output_overrides={
                    "outfit_slot_focus_points": [
                        {
                            "slot_role": "garment_photo",
                            "garment_type": "shirt",
                            "focus_points": ["Tuck the shirt into the waistband."],
                            "generation_exclusions": ["do not keep shirt untucked"],
                        }
                    ]
                }
            )
        ),
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(TryOnInstructionFailure) as exc_info:
        await adapter.create(
            job_id="try_on_1",
            analysis_bundle=approved_analysis_bundle(),
            wear_control_selections=[
                TryOnWearControlSelection(
                    slot_role="garment_photo",
                    garment_type="shirt",
                    requested_control_code="untucked",
                    resolved_control_code="untucked",
                    display_name="Untucked",
                    instruction_template="Keep the shirt hem visible over the waistband.",
                    risk_level="low",
                    resolved_by="user_selection",
                )
            ],
        )

    assert exc_info.value.safe_code == "wear_control_instruction_conflict"


@pytest.mark.anyio
async def test_instruction_agent_fails_closed_below_minimum_confidence() -> None:
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=_InvocationServiceStub(_envelope(confidence=0.4)),
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(TryOnInstructionFailure) as exc_info:
        await adapter.create(job_id="try_on_1", analysis_bundle=approved_analysis_bundle())

    assert exc_info.value.safe_code == "confidence_below_minimum"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("output_overrides", "safe_code"),
    [
        ({"preserve_face": False}, "preserve_face_disabled"),
        ({"preserve_body_shape": False}, "preserve_body_shape_disabled"),
        ({"preserve_pose": False}, "preserve_pose_disabled"),
        ({"garment_focus_points": []}, "garment_focus_points_missing"),
        ({"generation_exclusions": []}, "generation_exclusions_missing"),
        ({"evidence": []}, "instruction_evidence_missing"),
        ({"uncertainty_level": "high"}, "uncertainty_too_high"),
    ],
)
async def test_instruction_agent_blocks_unsafe_generation_instructions(
    output_overrides: dict[str, object],
    safe_code: str,
) -> None:
    adapter = TryOnInstructionAgentAdapter(
        invocation_service=_InvocationServiceStub(_envelope(output_overrides=output_overrides)),
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(TryOnInstructionFailure) as exc_info:
        await adapter.create(job_id="try_on_1", analysis_bundle=approved_analysis_bundle())

    assert exc_info.value.safe_code == safe_code
