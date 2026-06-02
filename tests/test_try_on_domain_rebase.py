from __future__ import annotations

from src.domain.try_on import TryOnGenerationMode, TryOnStoredInput, TryOnUploadRole


def test_try_on_stored_input_supports_portable_storage_backends() -> None:
    stored_input = TryOnStoredInput(
        role=TryOnUploadRole.HUMAN_PHOTO,
        storage_backend="s3",
        uri="s3://bucket/key",
        object_key="tenant/job/human.png",
        content_type="image/png",
        size_bytes=10,
        sha256="a" * 64,
    )

    assert stored_input.storage_backend == "s3"


def test_try_on_generation_mode_defaults_to_sandbox_fake() -> None:
    assert TryOnGenerationMode.SANDBOX_FAKE == "sandbox_fake"
