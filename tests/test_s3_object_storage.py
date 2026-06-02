from __future__ import annotations

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.storage.s3_object_storage import S3ObjectStorage


class _FakeS3Client:
    """Tiny fake S3 client used to validate adapter behavior."""

    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.presign_calls: list[dict[str, object]] = []
        self.get_calls: list[dict[str, object]] = []

    def put_object(self, **kwargs: object) -> dict[str, object]:
        self.put_calls.append(kwargs)
        return {"ETag": '"etag-123"', "VersionId": "version-1"}

    def generate_presigned_url(self, *, ClientMethod: str, Params: dict[str, str], ExpiresIn: int) -> str:
        self.presign_calls.append(
            {
                "ClientMethod": ClientMethod,
                "Params": Params,
                "ExpiresIn": ExpiresIn,
            }
        )
        return "https://signed.example/object"

    def get_object(self, **kwargs: object) -> dict[str, object]:
        self.get_calls.append(kwargs)
        return {"Body": _FakeBody(b"stored-image-bytes")}


class _FakeBody:
    """Simple streaming body stub for S3 get_object tests."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        """Return the configured bytes payload."""
        return self._payload


def test_in_memory_object_storage_returns_stable_object_key() -> None:
    storage = InMemoryObjectStorage()

    result = storage.put_bytes(
        object_key="try-on/jobs/job-1/result.png",
        payload=b"png",
        content_type="image/png",
    )

    assert result.object_key == "try-on/jobs/job-1/result.png"
    assert result.content_type == "image/png"


def test_in_memory_storage_can_return_signed_get_url() -> None:
    storage = InMemoryObjectStorage()
    stored = storage.put_bytes(
        object_key="fitfabrica/tenants/public/try-on/job-1/human_photo/photo.jpg",
        payload=b"image-bytes",
        content_type="image/jpeg",
    )

    signed = storage.create_signed_get_url(stored.object_key, expires_in_seconds=900)

    assert signed.method == "GET"
    assert signed.url == "memory://fitfabrica/tenants/public/try-on/job-1/human_photo/photo.jpg"


def test_in_memory_storage_can_read_back_stored_bytes() -> None:
    storage = InMemoryObjectStorage()
    stored = storage.put_bytes(
        object_key="fitfabrica/tenants/public/try-on/job-1/human_photo/photo.jpg",
        payload=b"image-bytes",
        content_type="image/jpeg",
    )

    payload = storage.get_bytes(stored.object_key)

    assert payload == b"image-bytes"


def test_s3_storage_returns_bucket_metadata_and_presigned_url(monkeypatch) -> None:
    fake_client = _FakeS3Client()
    monkeypatch.setattr(
        "src.adapters.storage.s3_object_storage.S3ObjectStorage._build_client",
        lambda *_args, **_kwargs: fake_client,
    )
    storage = S3ObjectStorage(
        bucket_name="fitfabrica-media",
        endpoint_url="https://s3.example.com",
        region_name="ru-central1",
        access_key_id="key",
        secret_access_key="secret",
    )

    stored = storage.put_bytes(
        object_key="fitfabrica/tenants/public/try-on/job-1/result.png",
        payload=b"png",
        content_type="image/png",
    )
    signed = storage.create_signed_get_url(stored.object_key, expires_in_seconds=900)

    assert stored.bucket_name == "fitfabrica-media"
    assert stored.object_key == "fitfabrica/tenants/public/try-on/job-1/result.png"
    assert stored.content_length == 3
    assert stored.etag == "etag-123"
    assert stored.version_id == "version-1"
    assert signed.url == "https://signed.example/object"
    assert signed.method == "GET"


def test_s3_storage_can_read_back_stored_bytes(monkeypatch) -> None:
    fake_client = _FakeS3Client()
    monkeypatch.setattr(
        "src.adapters.storage.s3_object_storage.S3ObjectStorage._build_client",
        lambda *_args, **_kwargs: fake_client,
    )
    storage = S3ObjectStorage(
        bucket_name="fitfabrica-media",
        endpoint_url="https://s3.example.com",
        region_name="ru-central1",
        access_key_id="key",
        secret_access_key="secret",
    )

    payload = storage.get_bytes("fitfabrica/tenants/public/try-on/job-1/result.png")

    assert payload == b"stored-image-bytes"
    assert fake_client.get_calls == [
        {"Bucket": "fitfabrica-media", "Key": "fitfabrica/tenants/public/try-on/job-1/result.png"}
    ]


def test_s3_storage_fails_with_clear_error_when_boto3_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.storage.s3_object_storage.importlib.import_module",
        lambda _name: (_ for _ in ()).throw(ModuleNotFoundError("No module named 'boto3'")),
    )

    import pytest

    with pytest.raises(RuntimeError, match="boto3 is required"):
        S3ObjectStorage(
            bucket_name="fitfabrica-media",
            endpoint_url="https://s3.example.com",
            region_name="ru-central1",
            access_key_id="key",
            secret_access_key="secret",
        )
