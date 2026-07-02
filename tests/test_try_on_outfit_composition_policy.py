from __future__ import annotations

import pytest
from starlette.datastructures import UploadFile
from io import BytesIO

from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnErrorCode, TryOnUploadRole
from src.domain.try_on_outfit import TryOnOutfitCompositionDecision
from src.use_cases.try_on.outfit_composition_policy import evaluate_outfit_composition
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnValidationError, TryOnWorkflowService
from tests.try_on_analysis_bundle_stub import required_analysis_bundle
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub


def test_outfit_composition_allows_legacy_single_item() -> None:
    verdict = evaluate_outfit_composition([TryOnUploadRole.GARMENT_PHOTO])

    assert verdict.decision == TryOnOutfitCompositionDecision.ALLOW
    assert verdict.reasons == []


def test_outfit_composition_allows_upper_lower_and_outerwear() -> None:
    verdict = evaluate_outfit_composition(
        [
            TryOnUploadRole.UPPER_GARMENT_PHOTO,
            TryOnUploadRole.LOWER_GARMENT_PHOTO,
            TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO,
        ]
    )

    assert verdict.decision == TryOnOutfitCompositionDecision.ALLOW
    assert verdict.warnings == []


def test_outfit_composition_blocks_full_body_with_separate_slots() -> None:
    verdict = evaluate_outfit_composition(
        [
            TryOnUploadRole.FULL_BODY_GARMENT_PHOTO,
            TryOnUploadRole.UPPER_GARMENT_PHOTO,
        ]
    )

    assert verdict.decision == TryOnOutfitCompositionDecision.BLOCK
    assert "full_body_conflicts_with_separate_slots" in verdict.reasons


def test_outfit_composition_blocks_outerwear_without_base_outfit() -> None:
    verdict = evaluate_outfit_composition([TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO])

    assert verdict.decision == TryOnOutfitCompositionDecision.BLOCK
    assert "base_outfit_required_for_outerwear" in verdict.reasons


def test_outfit_composition_blocks_duplicate_slots() -> None:
    verdict = evaluate_outfit_composition(
        [
            TryOnUploadRole.UPPER_GARMENT_PHOTO,
            TryOnUploadRole.UPPER_GARMENT_PHOTO,
        ]
    )

    assert verdict.decision == TryOnOutfitCompositionDecision.BLOCK
    assert "duplicate_garment_slot" in verdict.reasons


@pytest.mark.anyio
async def test_workflow_service_blocks_invalid_outfit_before_persistence() -> None:
    service = _service()

    with pytest.raises(TryOnValidationError) as exc_info:
        await service.create_job(
            human_photo=_upload_file("human.png", b"human-image", "image/png"),
            garment_photo=None,
            upper_garment_photo=_upload_file("upper.png", b"upper-image", "image/png"),
            full_body_garment_photo=_upload_file("dress.png", b"dress-image", "image/png"),
        )

    assert exc_info.value.error.code == TryOnErrorCode.INVALID_GARMENT_COMBINATION
    assert "full_body_conflicts_with_separate_slots" in exc_info.value.error.details["reasons"]


def _service() -> TryOnWorkflowService:
    return TryOnWorkflowService(
        repository=InMemoryTryOnJobRepository(),
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )


def _upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})
