from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.adapters.cache.redis_client import build_redis_client
from src.adapters.storage.s3_object_storage import S3ObjectStorage
from src.adapters.vector.qdrant_client import build_qdrant_client


def test_build_qdrant_client_fails_with_clear_error_when_dependency_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.vector.qdrant_client.importlib.import_module",
        lambda _name: (_ for _ in ()).throw(ModuleNotFoundError("No module named 'qdrant_client'")),
    )

    with pytest.raises(RuntimeError, match="qdrant_client is required"):
        build_qdrant_client(
            SimpleNamespace(
                qdrant_url="http://localhost:6333",
                qdrant_api_key=None,
                qdrant_request_timeout_seconds=10.0,
            )
        )


def test_build_redis_client_fails_with_clear_error_when_dependency_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.adapters.cache.redis_client.importlib.import_module",
        lambda _name: (_ for _ in ()).throw(ModuleNotFoundError("No module named 'redis'")),
    )

    with pytest.raises(RuntimeError, match="redis is required"):
        build_redis_client(SimpleNamespace(redis_url="redis://localhost:6379/0"))


def test_storage_package_can_be_imported_without_boto3() -> None:
    import src.adapters.storage as storage

    assert storage.InMemoryObjectStorage is not None
    assert storage.S3ObjectStorage is S3ObjectStorage
