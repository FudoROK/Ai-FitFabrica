from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from src.adapters.agents.try_on_garment_identity_analysis import select_primary_garment_input
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from src.use_cases.try_on.workflow_upload_validation import missing_fields
from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from tests.try_on_analysis_bundle_stub import required_analysis_bundle
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub
from src.main import app


def test_try_on_upload_roles_include_outfit_slots() -> None:
    assert TryOnUploadRole.UPPER_GARMENT_PHOTO.value == "upper_garment_photo"
    assert TryOnUploadRole.LOWER_GARMENT_PHOTO.value == "lower_garment_photo"
    assert TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO.value == "outerwear_garment_photo"
    assert TryOnUploadRole.FULL_BODY_GARMENT_PHOTO.value == "full_body_garment_photo"


def test_missing_fields_accepts_legacy_single_garment() -> None:
    assert missing_fields(human_photo=object(), garment_photo=object()) == []


def test_missing_fields_requires_human_and_at_least_one_garment_slot() -> None:
    assert missing_fields(human_photo=None, garment_photo=None) == ["human_photo", "garment_photo"]
    assert missing_fields(human_photo=object(), garment_photo=None) == ["garment_photo"]


def test_missing_fields_accepts_upper_and_lower_slots() -> None:
    assert (
        missing_fields(
            human_photo=object(),
            garment_photo=None,
            upper_garment_photo=object(),
            lower_garment_photo=object(),
        )
        == []
    )


@pytest.mark.anyio
async def test_try_on_workflow_service_persists_upper_and_lower_slots() -> None:
    service = _service()

    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=None,
        upper_garment_photo=_upload_file("upper.png", b"upper-image", "image/png"),
        lower_garment_photo=_upload_file("lower.webp", b"lower-image", "image/webp"),
    )

    assert [metadata.role for metadata in job.input_metadata] == [
        TryOnUploadRole.HUMAN_PHOTO,
        TryOnUploadRole.UPPER_GARMENT_PHOTO,
        TryOnUploadRole.LOWER_GARMENT_PHOTO,
    ]
    assert [stored.role for stored in job.stored_inputs] == [
        TryOnUploadRole.HUMAN_PHOTO,
        TryOnUploadRole.UPPER_GARMENT_PHOTO,
        TryOnUploadRole.LOWER_GARMENT_PHOTO,
    ]


def test_primary_garment_selector_prefers_legacy_then_full_body_then_slots() -> None:
    assert select_primary_garment_input([_stored(TryOnUploadRole.GARMENT_PHOTO)]).role == TryOnUploadRole.GARMENT_PHOTO
    assert (
        select_primary_garment_input(
            [
                _stored(TryOnUploadRole.LOWER_GARMENT_PHOTO),
                _stored(TryOnUploadRole.FULL_BODY_GARMENT_PHOTO),
                _stored(TryOnUploadRole.UPPER_GARMENT_PHOTO),
            ]
        ).role
        == TryOnUploadRole.FULL_BODY_GARMENT_PHOTO
    )


def test_try_on_route_accepts_upper_and_lower_slots_without_legacy_garment() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.png", b"human-image", "image/png"),
            "upper_garment_photo": ("upper.png", b"upper-image", "image/png"),
            "lower_garment_photo": ("lower.webp", b"lower-image", "image/webp"),
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert [item["role"] for item in body["input_metadata"]] == [
        "human_photo",
        "upper_garment_photo",
        "lower_garment_photo",
    ]
    assert (
        select_primary_garment_input(
            [
                _stored(TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO),
                _stored(TryOnUploadRole.LOWER_GARMENT_PHOTO),
                _stored(TryOnUploadRole.UPPER_GARMENT_PHOTO),
            ]
        ).role
        == TryOnUploadRole.UPPER_GARMENT_PHOTO
    )


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


def _stored(role: TryOnUploadRole) -> TryOnStoredInput:
    return TryOnStoredInput(
        role=role,
        storage_backend="s3",
        uri=f"s3://bucket/{role.value}.png",
        bucket_name="bucket",
        object_key=f"{role.value}.png",
        content_type="image/png",
        size_bytes=10,
        sha256="a" * 64,
    )
