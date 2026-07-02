from __future__ import annotations

import pytest

from src.adapters.agents.object_storage_artifact_resolver import ObjectStorageAgentArtifactResolver
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.domain.agent_runtime import AgentArtifactReference, AgentProviderFailure


def _reference(*, sha256: str, size_bytes: int) -> AgentArtifactReference:
    return AgentArtifactReference(
        purpose="human_photo",
        object_key="public/try-on/job/human.png",
        content_type="image/png",
        size_bytes=size_bytes,
        sha256=sha256,
    )


def test_object_storage_agent_artifact_resolver_returns_verified_transient_bytes() -> None:
    storage = InMemoryObjectStorage()
    payload = b"real-image-bytes"
    stored = storage.put_bytes(
        object_key="public/try-on/job/human.png",
        payload=payload,
        content_type="image/png",
    )
    resolver = ObjectStorageAgentArtifactResolver(object_storage=storage, max_artifact_bytes=1024)

    artifact = resolver.resolve(
        _reference(
            sha256=__import__("hashlib").sha256(payload).hexdigest(),
            size_bytes=stored.content_length,
        )
    )

    assert artifact.payload == payload
    assert artifact.content_type == "image/png"
    assert artifact.purpose == "human_photo"


def test_object_storage_agent_artifact_resolver_rejects_tampered_artifact() -> None:
    storage = InMemoryObjectStorage()
    storage.put_bytes(
        object_key="public/try-on/job/human.png",
        payload=b"real-image-bytes",
        content_type="image/png",
    )
    resolver = ObjectStorageAgentArtifactResolver(object_storage=storage, max_artifact_bytes=1024)

    with pytest.raises(AgentProviderFailure) as exc_info:
        resolver.resolve(_reference(sha256="a" * 64, size_bytes=16))

    assert exc_info.value.code == "artifact_integrity_failed"
