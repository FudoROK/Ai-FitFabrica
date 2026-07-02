"""Ports owned by the backend agent invocation layer."""

from __future__ import annotations

from typing import Protocol

from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRecord, AgentInvocationRequest, AgentProviderResult
from src.llm.core.request import LLMArtifact


class AgentInvocationPort(Protocol):
    """Provider-neutral gateway used by workflows to invoke one agent."""

    async def invoke(self, request: AgentInvocationRequest) -> AgentProviderResult:
        """Invoke one approved agent and return its structured provider result."""


class AgentInvocationRepositoryPort(Protocol):
    """Durable audit repository for backend-owned agent invocations."""

    async def save(self, record: AgentInvocationRecord) -> None:
        """Persist one safe final invocation audit record."""


class AgentArtifactResolverPort(Protocol):
    """Resolve one approved durable reference into a transient provider artifact."""

    def resolve(self, reference: AgentArtifactReference) -> LLMArtifact:
        """Load and integrity-check one approved artifact."""
