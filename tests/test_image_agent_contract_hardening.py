from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.adk_agents.fashion_stylist_agent.contracts import FashionStylistRequest
from src.adk_agents.garment_identity_agent.contracts import GarmentIdentityRequest
from src.adk_agents.human_identity_agent.contracts import HumanIdentityRequest
from src.adk_agents.material_texture_agent.contracts import MaterialTextureRequest
from src.adk_agents.material_texture_agent.contracts import MaterialTextureContract
from src.adk_agents.quality_verifier_agent.contracts import QualityVerifierDecisionContract, QualityVerifierRequest
from src.adk_agents.repair_agent.contracts import RepairAgentRequest, RepairInstructionContract
from src.adk_agents.try_on_agent.contracts import TryOnInstructionRequest


def test_image_agent_request_contracts_accept_only_backend_artifact_references() -> None:
    human = HumanIdentityRequest(human_photo_object_key="try-on/job-1/human.jpg")
    garment = GarmentIdentityRequest(garment_photo_object_key="try-on/job-1/garment.jpg")
    material = MaterialTextureRequest(garment_photo_object_key="try-on/job-1/garment.jpg")
    try_on = TryOnInstructionRequest(
        human_analysis={"face_visibility": "fully_visible"},
        garment_analysis={"garment_type": "dress"},
        material_analysis={"composition_status": "unknown"},
    )
    verifier = QualityVerifierRequest(
        human_photo_object_key="try-on/job-1/human.jpg",
        garment_photo_object_key="try-on/job-1/garment.jpg",
        generated_image_object_key="try-on/job-1/result.jpg",
    )
    repair = RepairAgentRequest(
        generated_image_object_key="try-on/job-1/result.jpg",
        approved_defects=[{"defect_type": "collar", "region": "neckline", "evidence": "collar edge is broken"}],
    )
    stylist = FashionStylistRequest(
        final_image_object_key="try-on/job-1/final.jpg",
        approved_style_facts=["clean neckline", "balanced silhouette"],
    )

    assert human.human_photo_object_key.endswith("human.jpg")
    assert garment.garment_photo_object_key.endswith("garment.jpg")
    assert material.garment_photo_object_key.endswith("garment.jpg")
    assert try_on.garment_analysis["garment_type"] == "dress"
    assert verifier.generated_image_object_key.endswith("result.jpg")
    assert repair.approved_defects[0].region == "neckline"
    assert stylist.approved_style_facts[0] == "clean neckline"


@pytest.mark.parametrize(
    ("contract", "payload"),
    [
        (HumanIdentityRequest, {"human_photo_object_key": ""}),
        (GarmentIdentityRequest, {"garment_photo_object_key": ""}),
        (MaterialTextureRequest, {"garment_photo_object_key": ""}),
        (TryOnInstructionRequest, {"human_analysis": {}, "garment_analysis": {}, "material_analysis": {}}),
        (
            QualityVerifierRequest,
            {
                "human_photo_object_key": "human.jpg",
                "garment_photo_object_key": "garment.jpg",
                "generated_image_object_key": "",
            },
        ),
        (RepairAgentRequest, {"generated_image_object_key": "result.jpg", "approved_defects": []}),
        (FashionStylistRequest, {"final_image_object_key": "final.jpg", "approved_style_facts": []}),
    ],
)
def test_image_agent_request_contracts_reject_missing_required_evidence(contract, payload) -> None:
    with pytest.raises(ValidationError):
        contract.model_validate(payload)


def test_quality_verifier_rejects_pass_verdict_with_blocking_defect() -> None:
    with pytest.raises(ValidationError):
        QualityVerifierDecisionContract(
            verdict="pass",
            summary="Incorrectly marked as pass.",
            confidence=0.9,
            defects=[
                {
                    "defect_type": "face",
                    "region": "face",
                    "severity": "blocking",
                    "evidence": "source face does not match generated result",
                    "repairable": False,
                    "confidence": 0.95,
                }
            ],
        )


def test_repair_contract_rejects_local_scope_without_region_instructions() -> None:
    with pytest.raises(ValidationError):
        RepairInstructionContract(
            repair_scope="local",
            target_issues=["broken collar"],
            editing_instructions=["repair collar"],
            confidence=0.8,
        )


def test_material_contract_rejects_trusted_composition_without_trusted_evidence() -> None:
    with pytest.raises(ValidationError):
        MaterialTextureContract(
            visible_material_signals=["soft drape"],
            texture_signals=["smooth"],
            evidence_note="Visual estimate only.",
            composition_status="trusted_fact_provided",
            confidence=0.7,
        )
