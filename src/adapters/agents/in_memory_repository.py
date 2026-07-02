"""In-memory agent invocation audit repository for isolated tests."""

from __future__ import annotations

from src.domain.agent_runtime import AgentInvocationRecord


class InMemoryAgentInvocationRepository:
    """Store agent invocation audit records in memory for test environments."""

    def __init__(self) -> None:
        """Initialize the isolated audit record store."""

        self._records: dict[str, AgentInvocationRecord] = {}

    async def save(self, record: AgentInvocationRecord) -> None:
        """Store one final invocation audit record."""

        self._records[record.invocation_id] = record

    async def get(self, *, invocation_id: str) -> AgentInvocationRecord | None:
        """Return one stored invocation audit record."""

        return self._records.get(invocation_id)

