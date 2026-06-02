"""Portable infrastructure bootstrap container."""

from __future__ import annotations

from dataclasses import dataclass

from src.adapters.cache.redis_client import build_redis_client
from src.adapters.database.sql.engine import build_async_engine
from src.adapters.database.sql.session import build_session_factory
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.storage.s3_object_storage import S3ObjectStorage
from src.adapters.vector.qdrant_client import build_qdrant_client


@dataclass
class PortableInfrastructure:
    """Runtime-owned handles for portable infrastructure dependencies."""

    sql_engine: object | None
    sql_session_factory: object | None
    redis_client: object | None
    object_storage: object
    qdrant_client: object | None


def build_portable_infrastructure(settings) -> PortableInfrastructure:
    """Build portable infrastructure handles from the current settings snapshot."""
    postgres_dsn = getattr(settings, "postgres_dsn", None)
    redis_url = getattr(settings, "redis_url", None)
    object_storage_backend = getattr(settings, "object_storage_backend", "in_memory")
    qdrant_url = getattr(settings, "qdrant_url", None)

    sql_engine = build_async_engine(settings) if postgres_dsn else None
    sql_session_factory = build_session_factory(sql_engine) if sql_engine is not None else None
    redis_client = build_redis_client(settings) if redis_url else None

    if object_storage_backend == "s3":
        object_storage = S3ObjectStorage(
            bucket_name=getattr(settings, "object_storage_bucket_name", None),
            endpoint_url=getattr(settings, "object_storage_endpoint_url", None),
            region_name=getattr(settings, "object_storage_region", None),
            access_key_id=getattr(settings, "object_storage_access_key_id", None),
            secret_access_key=getattr(settings, "object_storage_secret_access_key", None),
        )
    else:
        object_storage = InMemoryObjectStorage()

    qdrant_client = build_qdrant_client(settings) if qdrant_url else None

    return PortableInfrastructure(
        sql_engine=sql_engine,
        sql_session_factory=sql_session_factory,
        redis_client=redis_client,
        object_storage=object_storage,
        qdrant_client=qdrant_client,
    )
