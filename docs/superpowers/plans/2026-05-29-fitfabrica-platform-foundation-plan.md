# AI FitFabrica Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the portable infrastructure foundation for AI FitFabrica so PostgreSQL, Redis, S3-compatible object storage, and Qdrant exist as first-class runtime dependencies before any feature workflow is migrated onto them.

**Architecture:** This stage does not migrate business workflows yet. It introduces neutral infrastructure packages, validated settings, bootstrap wiring, smoke checks, and health reporting while isolating old Firestore/GCS usage as migration-state code. Existing feature code may remain temporarily on legacy adapters, but new infrastructure code must not depend on Google persistence or storage SDKs.

**Tech Stack:** FastAPI, Pydantic Settings, SQLAlchemy, Alembic, asyncpg, redis-py, boto3, qdrant-client, pytest.

---

## Scope Boundary

This plan covers only Stage 1 foundation work:

- PostgreSQL runtime bootstrap
- Alembic migration foundation
- Redis runtime bootstrap and rate limiter migration
- S3-compatible object storage contract and first adapter
- Qdrant client bootstrap and collection initialization
- health/smoke verification for the new infrastructure

This plan does not cover:

- migrating identity data out of Firestore
- migrating Try-On jobs to PostgreSQL/S3
- product search business logic
- provider abstraction work

## File Structure

### New files

- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/20260529_000001_platform_foundation_baseline.py`
- `src/adapters/database/sql/__init__.py`
- `src/adapters/database/sql/base.py`
- `src/adapters/database/sql/engine.py`
- `src/adapters/database/sql/session.py`
- `src/adapters/database/sql/models.py`
- `src/adapters/database/sql/health.py`
- `src/adapters/cache/__init__.py`
- `src/adapters/cache/redis_client.py`
- `src/adapters/storage/__init__.py`
- `src/adapters/storage/contracts.py`
- `src/adapters/storage/in_memory_object_storage.py`
- `src/adapters/storage/s3_object_storage.py`
- `src/adapters/vector/__init__.py`
- `src/adapters/vector/contracts.py`
- `src/adapters/vector/qdrant_client.py`
- `src/adapters/vector/qdrant_index.py`
- `src/services/rate_limit/redis_rate_limiter.py`
- `src/services/runtime/portable_infrastructure.py`
- `scripts/platform_foundation_smoke.py`
- `tests/test_portable_platform_settings.py`
- `tests/test_sqlalchemy_runtime.py`
- `tests/test_redis_rate_limiter_factory.py`
- `tests/test_s3_object_storage.py`
- `tests/test_qdrant_bootstrap.py`
- `tests/test_platform_foundation_smoke.py`
- `tests/architecture/test_portable_foundation_guardrails.py`

### Modified files

- `requirements.txt`
- `requirements-dev.txt`
- `.env.example`
- `README.md`
- `src/settings.py`
- `src/main.py`
- `src/entrypoints/runtime_dependencies.py`
- `src/entrypoints/status_routes.py`
- `src/services/rate_limit/factory.py`
- `tests/test_settings.py`
- `tests/test_runtime_dependencies_container.py`

## Task 1: Define Portable Settings And Dependencies

**Files:**
- Modify: `requirements.txt`
- Modify: `.env.example`
- Modify: `src/settings.py`
- Create: `tests/test_portable_platform_settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write the failing portable-settings tests**

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.settings import Settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "gcp_project_id": "test-project",
        "pubsub_topic_name": "agent-jobs",
        "messaging_provider": "none",
    }
    values.update(overrides)
    return Settings(**values)


def test_portable_backends_default_to_postgres_redis_s3_qdrant_ready_settings() -> None:
    settings = _settings()

    assert settings.rate_limit_backend == "redis"
    assert settings.object_storage_backend == "in_memory"
    assert settings.vector_backend == "qdrant"
    assert settings.postgres_dsn is None


def test_s3_backend_requires_bucket_name() -> None:
    with pytest.raises(ValidationError, match="object_storage_bucket_name"):
        _settings(object_storage_backend="s3")


def test_qdrant_backend_requires_url() -> None:
    with pytest.raises(ValidationError, match="qdrant_url"):
        _settings(vector_backend="qdrant", qdrant_url="   ")


def test_postgres_settings_accept_database_url_alias() -> None:
    settings = _settings(DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/fitfabrica")
    assert settings.postgres_dsn == "postgresql+asyncpg://user:pass@localhost:5432/fitfabrica"
```

- [ ] **Step 2: Run the new settings tests and confirm they fail**

Run:

```bash
pytest tests/test_portable_platform_settings.py -q
```

Expected:

```text
E   AttributeError: 'Settings' object has no attribute 'object_storage_backend'
```

- [ ] **Step 3: Add portable dependencies to runtime requirements**

Update `requirements.txt` with:

```text
sqlalchemy==2.0.44
alembic==1.17.1
asyncpg==0.30.0
redis==6.4.0
boto3==1.40.59
qdrant-client==1.15.1
```

- [ ] **Step 4: Extend `src/settings.py` with portable foundation fields and validators**

Add fields and validators shaped like:

```python
postgres_dsn: str | None = Field(default=None, validation_alias=AliasChoices("POSTGRES_DSN", "DATABASE_URL"))
postgres_pool_size: int = 10
postgres_max_overflow: int = 20
postgres_pool_timeout_seconds: int = 30

redis_url: str | None = Field(default=None, validation_alias=AliasChoices("REDIS_URL"))
redis_key_prefix: str = "fitfabrica"

object_storage_backend: Literal["in_memory", "s3"] = "in_memory"
object_storage_bucket_name: str | None = Field(default=None, validation_alias=AliasChoices("OBJECT_STORAGE_BUCKET_NAME"))
object_storage_region: str | None = Field(default=None, validation_alias=AliasChoices("OBJECT_STORAGE_REGION"))
object_storage_endpoint_url: str | None = Field(default=None, validation_alias=AliasChoices("OBJECT_STORAGE_ENDPOINT_URL"))
object_storage_access_key_id: str | None = Field(default=None, validation_alias=AliasChoices("OBJECT_STORAGE_ACCESS_KEY_ID"))
object_storage_secret_access_key: str | None = Field(default=None, validation_alias=AliasChoices("OBJECT_STORAGE_SECRET_ACCESS_KEY"))
object_storage_prefix: str = "fitfabrica"

vector_backend: Literal["qdrant"] = "qdrant"
qdrant_url: str | None = Field(default=None, validation_alias=AliasChoices("QDRANT_URL"))
qdrant_api_key: str | None = Field(default=None, validation_alias=AliasChoices("QDRANT_API_KEY"))
qdrant_collection_prefix: str = "fitfabrica"
qdrant_request_timeout_seconds: float = 10.0
```

Add validation rules:

```python
if self.object_storage_backend == "s3" and not bucket_name:
    raise ValueError("object_storage_bucket_name is required when object_storage_backend is s3")
if self.vector_backend == "qdrant" and not qdrant_url:
    raise ValueError("qdrant_url is required when vector_backend is qdrant")
if self.rate_limit_backend == "redis" and not redis_url:
    raise ValueError("redis_url is required when rate_limit_backend is redis")
```

Also change the existing rate-limit backend validator to:

```python
if normalized not in {"redis", "inmemory"}:
    raise ValueError("RATE_LIMIT_BACKEND must be one of: redis, inmemory")
```

- [ ] **Step 5: Add environment examples for the new portable baseline**

Add this block to `.env.example`:

```dotenv
POSTGRES_DSN=postgresql+asyncpg://fitfabrica:fitfabrica@localhost:5432/fitfabrica
REDIS_URL=redis://localhost:6379/0
OBJECT_STORAGE_BUCKET_NAME=fitfabrica
OBJECT_STORAGE_REGION=us-east-1
OBJECT_STORAGE_ENDPOINT_URL=http://localhost:9000
OBJECT_STORAGE_ACCESS_KEY_ID=minioadmin
OBJECT_STORAGE_SECRET_ACCESS_KEY=minioadmin
OBJECT_STORAGE_PREFIX=fitfabrica
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_PREFIX=fitfabrica
RATE_LIMIT_BACKEND=redis
OBJECT_STORAGE_BACKEND=s3
VECTOR_BACKEND=qdrant
```

- [ ] **Step 6: Re-run settings coverage**

Run:

```bash
pytest tests/test_portable_platform_settings.py tests/test_settings.py -q
```

Expected:

```text
passed
```

## Task 2: Add PostgreSQL Runtime And Alembic Foundation

**Files:**
- Create: `src/adapters/database/sql/__init__.py`
- Create: `src/adapters/database/sql/base.py`
- Create: `src/adapters/database/sql/engine.py`
- Create: `src/adapters/database/sql/session.py`
- Create: `src/adapters/database/sql/models.py`
- Create: `src/adapters/database/sql/health.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`
- Create: `alembic/versions/20260529_000001_platform_foundation_baseline.py`
- Create: `tests/test_sqlalchemy_runtime.py`

- [ ] **Step 1: Write the failing SQL runtime tests**

```python
from __future__ import annotations

from src.adapters.database.sql.health import SqlHealthcheck
from src.adapters.database.sql.models import PortableRuntimeMetadataRow


def test_runtime_metadata_table_name_is_stable() -> None:
    assert PortableRuntimeMetadataRow.__tablename__ == "portable_runtime_metadata"


def test_sql_healthcheck_reports_component_name() -> None:
    health = SqlHealthcheck(engine=None)
    assert health.component_name == "postgresql"
```

- [ ] **Step 2: Run the SQL runtime tests and confirm they fail**

Run:

```bash
pytest tests/test_sqlalchemy_runtime.py -q
```

Expected:

```text
E   ModuleNotFoundError: No module named 'src.adapters.database.sql'
```

- [ ] **Step 3: Create the SQL base, engine, and session modules**

Implement these files:

```python
# src/adapters/database/sql/base.py
from sqlalchemy.orm import DeclarativeBase


class SqlBase(DeclarativeBase):
    pass
```

```python
# src/adapters/database/sql/engine.py
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def build_async_engine(settings) -> AsyncEngine:
    if not settings.postgres_dsn:
        raise ValueError("postgres_dsn is required to build the PostgreSQL engine")
    return create_async_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
        pool_timeout=settings.postgres_pool_timeout_seconds,
    )
```

```python
# src/adapters/database/sql/session.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def build_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

- [ ] **Step 4: Add a minimal runtime metadata model and health probe**

```python
# src/adapters/database/sql/models.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class PortableRuntimeMetadataRow(SqlBase):
    __tablename__ = "portable_runtime_metadata"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
```

```python
# src/adapters/database/sql/health.py
class SqlHealthcheck:
    component_name = "postgresql"

    def __init__(self, engine) -> None:
        self._engine = engine
```

- [ ] **Step 5: Add Alembic bootstrap files and one baseline migration**

Create `alembic/env.py` with target metadata import:

```python
from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql import models  # noqa: F401

target_metadata = SqlBase.metadata
```

Create initial migration with:

```python
def upgrade() -> None:
    op.create_table(
        "portable_runtime_metadata",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("portable_runtime_metadata")
```

- [ ] **Step 6: Verify SQL foundation tests**

Run:

```bash
pytest tests/test_sqlalchemy_runtime.py -q
```

Expected:

```text
2 passed
```

## Task 3: Add Redis Client Bootstrap And Move Rate Limiting Off Firestore

**Files:**
- Create: `src/adapters/cache/__init__.py`
- Create: `src/adapters/cache/redis_client.py`
- Create: `src/services/rate_limit/redis_rate_limiter.py`
- Modify: `src/services/rate_limit/factory.py`
- Create: `tests/test_redis_rate_limiter_factory.py`

- [ ] **Step 1: Write the failing Redis rate-limit tests**

```python
from __future__ import annotations

from types import SimpleNamespace

from src.services.rate_limit.factory import create_rate_limiter


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        enable_distributed_rate_limit=True,
        rate_limit_backend="redis",
        rate_limit_max_events=10,
        rate_limit_window_seconds=60,
        rate_limit_fail_mode="closed",
        rate_limit_collection="runtime_rate_limits",
        redis_url="redis://localhost:6379/0",
        redis_key_prefix="fitfabrica",
    )


def test_create_rate_limiter_builds_redis_backend(monkeypatch) -> None:
    monkeypatch.setattr("src.services.rate_limit.factory.build_redis_client", lambda settings: "redis-client")
    limiter = create_rate_limiter(_settings())
    assert limiter.__class__.__name__ == "FailModeRateLimiter"
```

- [ ] **Step 2: Run the Redis rate-limit tests and confirm they fail**

Run:

```bash
pytest tests/test_redis_rate_limiter_factory.py -q
```

Expected:

```text
E   ImportError: cannot import name 'build_redis_client'
```

- [ ] **Step 3: Add a Redis client builder**

Create `src/adapters/cache/redis_client.py`:

```python
from __future__ import annotations

from redis import Redis


def build_redis_client(settings) -> Redis:
    if not settings.redis_url:
        raise ValueError("redis_url is required to build the Redis client")
    return Redis.from_url(settings.redis_url, decode_responses=True)
```

- [ ] **Step 4: Implement a Redis-backed rate limiter and swap factory default**

Create `src/services/rate_limit/redis_rate_limiter.py`:

```python
from __future__ import annotations

import time

from .contracts import RateLimitDecision


class RedisRateLimiter:
    def __init__(self, *, redis_client, max_events: int, window_seconds: int, key_prefix: str) -> None:
        self._redis = redis_client
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._key_prefix = key_prefix

    def allow(self, key: str) -> RateLimitDecision:
        now = int(time.time())
        bucket_key = f"{self._key_prefix}:{key}"
        window_start = now - self._window_seconds
        pipeline = self._redis.pipeline()
        pipeline.zremrangebyscore(bucket_key, 0, window_start)
        pipeline.zcard(bucket_key)
        _, current_count = pipeline.execute()
        if int(current_count) >= self._max_events:
            return RateLimitDecision(
                status="denied_limit_exceeded",
                remaining=0,
                retry_after_seconds=self._window_seconds,
                reason="rate_limit_exceeded",
            )

        pipeline = self._redis.pipeline()
        pipeline.zadd(bucket_key, {f"{now}:{key}": now})
        pipeline.expire(bucket_key, self._window_seconds)
        pipeline.execute()
        remaining = max(self._max_events - int(current_count) - 1, 0)
        return RateLimitDecision(status="allowed", remaining=remaining)
```

Then update `src/services/rate_limit/factory.py` so the backend resolution becomes:

```python
elif not settings.enable_distributed_rate_limit:
    backend = "inmemory"
else:
    backend = (settings.rate_limit_backend or "redis").strip().lower()

if backend == "redis":
    limiter = RedisRateLimiter(
        redis_client=build_redis_client(settings),
        max_events=resolved_max_events,
        window_seconds=resolved_window_seconds,
        key_prefix=f"{settings.redis_key_prefix}:{resolved_collection_name}",
    )
elif backend == "inmemory":
    limiter = InMemoryRateLimiter(
        max_events=resolved_max_events,
        window_seconds=resolved_window_seconds,
    )
else:
    raise ValueError("Unsupported rate limit backend. Expected one of: redis, inmemory")
```

Remove the Firestore-specific import path from this file entirely.

- [ ] **Step 5: Verify Redis rate-limit factory coverage**

Run:

```bash
pytest tests/test_redis_rate_limiter_factory.py tests/test_runtime_dependencies_container.py tests/test_rate_limiter.py -q
```

Expected:

```text
passed
```

## Task 4: Add S3-Compatible Object Storage Contract And First Adapter

**Files:**
- Create: `src/adapters/storage/__init__.py`
- Create: `src/adapters/storage/contracts.py`
- Create: `src/adapters/storage/in_memory_object_storage.py`
- Create: `src/adapters/storage/s3_object_storage.py`
- Create: `tests/test_s3_object_storage.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing object storage tests**

```python
from __future__ import annotations

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage


def test_in_memory_object_storage_returns_stable_object_key() -> None:
    storage = InMemoryObjectStorage()
    result = storage.put_bytes(
        object_key="try-on/jobs/job-1/result.png",
        payload=b"png",
        content_type="image/png",
    )
    assert result.object_key == "try-on/jobs/job-1/result.png"
    assert result.content_type == "image/png"
```

- [ ] **Step 2: Run the object storage tests and confirm they fail**

Run:

```bash
pytest tests/test_s3_object_storage.py -q
```

Expected:

```text
E   ModuleNotFoundError: No module named 'src.adapters.storage'
```

- [ ] **Step 3: Define the neutral object storage contract**

Create `src/adapters/storage/contracts.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    content_type: str
    etag: str | None
    version_id: str | None
    storage_backend: str


class ObjectStorage(Protocol):
    def put_bytes(self, *, object_key: str, payload: bytes, content_type: str) -> StoredObject: ...
```

- [ ] **Step 4: Implement in-memory and S3 adapters**

Create `src/adapters/storage/in_memory_object_storage.py`:

```python
from __future__ import annotations

from .contracts import StoredObject


class InMemoryObjectStorage:
    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    def put_bytes(self, *, object_key: str, payload: bytes, content_type: str) -> StoredObject:
        self._objects[object_key] = (payload, content_type)
        return StoredObject(
            object_key=object_key,
            content_type=content_type,
            etag=None,
            version_id=None,
            storage_backend="in_memory",
        )
```

Create `src/adapters/storage/s3_object_storage.py`:

```python
from __future__ import annotations

import boto3

from .contracts import StoredObject


class S3ObjectStorage:
    def __init__(self, *, bucket_name: str, endpoint_url: str | None, region_name: str | None, access_key_id: str | None, secret_access_key: str | None) -> None:
        self._bucket_name = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
```

- [ ] **Step 5: Document the portable storage contract in `README.md`**

Add a section like:

```md
## Portable Runtime Dependencies

- PostgreSQL for canonical state
- Redis for rate limiting and short-lived coordination
- S3-compatible storage for binary artifacts
- Qdrant for vector retrieval
```

- [ ] **Step 6: Verify object storage tests**

Run:

```bash
pytest tests/test_s3_object_storage.py -q
```

Expected:

```text
passed
```

## Task 5: Add Qdrant Client Bootstrap And Collection Initialization

**Files:**
- Create: `src/adapters/vector/__init__.py`
- Create: `src/adapters/vector/contracts.py`
- Create: `src/adapters/vector/qdrant_client.py`
- Create: `src/adapters/vector/qdrant_index.py`
- Create: `tests/test_qdrant_bootstrap.py`

- [ ] **Step 1: Write the failing Qdrant bootstrap tests**

```python
from __future__ import annotations

from src.adapters.vector.qdrant_index import collection_name_for_namespace


def test_collection_name_for_namespace_uses_prefix() -> None:
    name = collection_name_for_namespace(prefix="fitfabrica", namespace="garments")
    assert name == "fitfabrica_garments"
```

- [ ] **Step 2: Run the Qdrant tests and confirm they fail**

Run:

```bash
pytest tests/test_qdrant_bootstrap.py -q
```

Expected:

```text
E   ModuleNotFoundError: No module named 'src.adapters.vector'
```

- [ ] **Step 3: Add the Qdrant client builder and collection naming helper**

Create `src/adapters/vector/qdrant_client.py`:

```python
from __future__ import annotations

from qdrant_client import QdrantClient


def build_qdrant_client(settings) -> QdrantClient:
    if not settings.qdrant_url:
        raise ValueError("qdrant_url is required to build the Qdrant client")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=settings.qdrant_request_timeout_seconds)
```

Create `src/adapters/vector/qdrant_index.py`:

```python
from __future__ import annotations


def collection_name_for_namespace(*, prefix: str, namespace: str) -> str:
    normalized_prefix = prefix.strip().replace("-", "_")
    normalized_namespace = namespace.strip().replace("-", "_")
    return f"{normalized_prefix}_{normalized_namespace}"
```

- [ ] **Step 4: Add a thin vector contract for later stages**

Create `src/adapters/vector/contracts.py`:

```python
from __future__ import annotations

from typing import Protocol


class VectorIndexBootstrapper(Protocol):
    def ensure_collection(self, *, namespace: str, vector_size: int) -> None: ...
```

- [ ] **Step 5: Verify Qdrant bootstrap coverage**

Run:

```bash
pytest tests/test_qdrant_bootstrap.py -q
```

Expected:

```text
passed
```

## Task 6: Wire Portable Infrastructure Into Runtime Bootstrap, Health, And Smoke Checks

**Files:**
- Create: `src/services/runtime/portable_infrastructure.py`
- Modify: `src/entrypoints/runtime_dependencies.py`
- Modify: `src/entrypoints/status_routes.py`
- Modify: `src/main.py`
- Create: `scripts/platform_foundation_smoke.py`
- Create: `tests/test_platform_foundation_smoke.py`
- Modify: `tests/test_runtime_dependencies_container.py`
- Create: `tests/architecture/test_portable_foundation_guardrails.py`

- [ ] **Step 1: Write the failing runtime bootstrap tests**

```python
from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints.runtime_dependencies import portable_infrastructure


def test_portable_infrastructure_is_cached_per_settings_instance(monkeypatch) -> None:
    settings = SimpleNamespace()
    first = portable_infrastructure(settings)
    second = portable_infrastructure(settings)
    assert first is second
```

- [ ] **Step 2: Run the runtime bootstrap tests and confirm they fail**

Run:

```bash
pytest tests/test_runtime_dependencies_container.py tests/test_platform_foundation_smoke.py -q
```

Expected:

```text
E   AttributeError: module 'src.entrypoints.runtime_dependencies' has no attribute 'portable_infrastructure'
```

- [ ] **Step 3: Add the portable infrastructure container**

Create `src/services/runtime/portable_infrastructure.py`:

```python
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
    sql_engine: object | None
    sql_session_factory: object | None
    redis_client: object | None
    object_storage: object
    qdrant_client: object | None
```

- [ ] **Step 4: Expose portable infrastructure through `runtime_dependencies.py`**

Add a cached accessor:

```python
_PORTABLE_INFRA_ATTR = "_portable_infrastructure"


def portable_infrastructure(settings):
    infrastructure = getattr(settings, _PORTABLE_INFRA_ATTR, None)
    if infrastructure is None:
        infrastructure = build_portable_infrastructure(settings)
        setattr(settings, _PORTABLE_INFRA_ATTR, infrastructure)
    return infrastructure
```

Do not remove the existing dialog container in this task. Keep legacy runtime wiring intact and add the portable wiring beside it.

- [ ] **Step 5: Extend `/health` to report portable component readiness**

Update `src/entrypoints/status_routes.py` to return:

```python
return JSONResponse(
    status_code=200,
    content={
        "status": "healthy",
        "infrastructure": {
            "postgresql": "configured" if settings.postgres_dsn else "not_configured",
            "redis": "configured" if settings.redis_url else "not_configured",
            "object_storage": settings.object_storage_backend,
            "qdrant": "configured" if settings.qdrant_url else "not_configured",
        },
    },
)
```

- [ ] **Step 6: Add a deterministic smoke script**

Create `scripts/platform_foundation_smoke.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.settings import load_settings


def main() -> int:
    settings = load_settings()
    print("platform_foundation_smoke")
    print(f"postgres_configured={str(bool(settings.postgres_dsn)).lower()}")
    print(f"redis_configured={str(bool(settings.redis_url)).lower()}")
    print(f"object_storage_backend={settings.object_storage_backend}")
    print(f"qdrant_backend={settings.vector_backend}")
    print(f"qdrant_configured={str(bool(settings.qdrant_url)).lower()}")
    return 0
```

- [ ] **Step 7: Add guardrails for the new infrastructure packages**

Create `tests/architecture/test_portable_foundation_guardrails.py` to assert:

```python
assert "google.cloud" not in text
assert "firestore" not in text
assert "gcs" not in text
```

for files under:

- `src/adapters/database/sql`
- `src/adapters/cache`
- `src/adapters/storage`
- `src/adapters/vector`

- [ ] **Step 8: Run the full Stage 1 verification set**

Run:

```bash
pytest \
  tests/test_portable_platform_settings.py \
  tests/test_sqlalchemy_runtime.py \
  tests/test_redis_rate_limiter_factory.py \
  tests/test_s3_object_storage.py \
  tests/test_qdrant_bootstrap.py \
  tests/test_platform_foundation_smoke.py \
  tests/test_runtime_dependencies_container.py \
  tests/architecture/test_portable_foundation_guardrails.py -q
```

Expected:

```text
passed
```

## Task 7: Finalize Documentation And Operator Handoff

**Files:**
- Modify: `README.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/project_description.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update active docs to reference the new foundation packages**

Document these exact runtime surfaces:

- `src/adapters/database/sql`
- `src/adapters/cache`
- `src/adapters/storage`
- `src/adapters/vector`
- `src/services/runtime/portable_infrastructure.py`

- [ ] **Step 2: Mark Stage 1 foundation plan as written in the master plan**

Add this line under Stage 1 in the master plan:

```md
- detailed plan: `docs/superpowers/plans/2026-05-29-fitfabrica-platform-foundation-plan.md`
```

- [ ] **Step 3: Run final document and smoke verification**

Run:

```bash
python scripts/platform_foundation_smoke.py
pytest tests/test_platform_foundation_smoke.py -q
```

Expected:

```text
platform_foundation_smoke
postgres_configured=true|false
redis_configured=true|false
object_storage_backend=in_memory|s3
qdrant_backend=qdrant
qdrant_configured=true|false
```

## Self-Review

Spec coverage check:

- PostgreSQL integration baseline: covered in Task 2 and Task 6
- migration framework: covered in Task 2
- repository and session foundation: covered in Task 2
- Redis integration baseline: covered in Task 3 and Task 6
- S3-compatible storage contract: covered in Task 4 and Task 6
- Qdrant client and collection contract: covered in Task 5 and Task 6

Placeholder scan:

- no `TODO`
- no `TBD`
- no “implement later” placeholders

Type consistency check:

- settings names are consistent across tasks: `postgres_dsn`, `redis_url`, `object_storage_backend`, `qdrant_url`
- runtime bootstrap naming is consistent: `portable_infrastructure`
- object storage contract naming is consistent: `StoredObject`, `ObjectStorage`

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-29-fitfabrica-platform-foundation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
