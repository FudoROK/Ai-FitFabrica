"""Idempotency boundary for retry-safe business catalog mutations."""

from __future__ import annotations

from typing import Protocol, TypeVar


T = TypeVar("T")


class BusinessCatalogIdempotencyStorePort(Protocol):
    """Storage boundary for successful idempotent catalog mutation results."""

    async def get(self, operation_key: str) -> object | None:
        """Return a cached successful operation result, if present."""

    async def save(self, operation_key: str, result: object) -> None:
        """Persist a successful operation result for future retries."""


class InMemoryBusinessCatalogIdempotencyStore:
    """In-memory idempotency store for tests and local sandbox usage."""

    def __init__(self) -> None:
        """Initialize an empty successful-result cache."""

        self._results: dict[str, object] = {}

    async def get(self, operation_key: str) -> object | None:
        """Return a cached successful operation result, if present."""

        return self._results.get(operation_key)

    async def save(self, operation_key: str, result: object) -> None:
        """Persist a successful operation result for future retries."""

        self._results[operation_key] = result


def scoped_idempotency_key(*, owner_id: str, operation: str, idempotency_key: str | None) -> str | None:
    """Build a stable owner-scoped key without exposing cross-owner state."""

    if idempotency_key is None or not idempotency_key.strip():
        return None
    return f"business-catalog:{owner_id}:{operation}:{idempotency_key.strip()}"


async def run_idempotent(
    *,
    store: BusinessCatalogIdempotencyStorePort | None,
    operation_key: str | None,
    operation,
) -> T:
    """Run one mutation once per successful idempotency key."""

    if store is None or operation_key is None:
        return await operation()
    cached = await store.get(operation_key)
    if cached is not None:
        return cached
    result = await operation()
    await store.save(operation_key, result)
    return result
