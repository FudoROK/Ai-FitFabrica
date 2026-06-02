"""Portable object storage adapters."""

from .contracts import ObjectStorage, SignedUrl, StoredObject
from .in_memory_object_storage import InMemoryObjectStorage
from .media_storage import TryOnMediaStorage
from .object_naming import build_media_object_key, normalize_storage_filename

__all__ = [
    "ObjectStorage",
    "SignedUrl",
    "StoredObject",
    "InMemoryObjectStorage",
    "S3ObjectStorage",
    "TryOnMediaStorage",
    "build_media_object_key",
    "normalize_storage_filename",
]


def __getattr__(name: str):
    """Load optional storage adapters lazily to avoid import-time dependency failures."""
    if name == "S3ObjectStorage":
        from .s3_object_storage import S3ObjectStorage

        return S3ObjectStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
