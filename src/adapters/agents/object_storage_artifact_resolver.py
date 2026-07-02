"""Resolve approved agent artifact references through backend-owned storage."""

from __future__ import annotations

from hashlib import sha256

from src.adapters.storage.contracts import ObjectStorage
from src.domain.agent_runtime import AgentArtifactReference, AgentProviderFailure
from src.llm.core.request import LLMArtifact


class ObjectStorageAgentArtifactResolver:
    """Load and integrity-check transient artifacts before provider invocation."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorage,
        max_artifact_bytes: int,
        allowed_content_types: set[str] | None = None,
    ) -> None:
        """Store the backend-owned object storage and safety policy."""

        self._object_storage = object_storage
        self._max_artifact_bytes = max_artifact_bytes
        self._allowed_content_types = allowed_content_types or {"image/jpeg", "image/png", "image/webp"}

    def resolve(self, reference: AgentArtifactReference) -> LLMArtifact:
        """Return verified bytes or fail closed without exposing storage details."""

        if reference.content_type not in self._allowed_content_types:
            raise self._failure("artifact_content_type_not_allowed")
        if reference.size_bytes > self._max_artifact_bytes:
            raise self._failure("artifact_too_large")
        try:
            payload = self._object_storage.get_bytes(reference.object_key)
        except Exception as exc:  # noqa: BLE001
            raise self._failure("artifact_unavailable", retriable=True) from exc
        if len(payload) != reference.size_bytes or sha256(payload).hexdigest() != reference.sha256:
            raise self._failure("artifact_integrity_failed")
        return LLMArtifact(
            purpose=reference.purpose,
            content_type=reference.content_type,
            payload=payload,
        )

    @staticmethod
    def _failure(code: str, *, retriable: bool = False) -> AgentProviderFailure:
        """Build a safe artifact-resolution failure."""

        return AgentProviderFailure(
            code=code,
            message="Approved agent artifact could not be resolved safely.",
            retriable=retriable,
        )
