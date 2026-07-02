"""SQL-backed repository for safe agent invocation audit records."""

from __future__ import annotations

from datetime import datetime, timezone

from src.domain.agent_runtime import AgentInvocationRecord

from .agent_invocation_models import AgentInvocationRow


class SqlAgentInvocationRepository:
    """Persist safe final agent invocation audit records."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""

        self._session_factory = session_factory

    async def save(self, record: AgentInvocationRecord) -> None:
        """Insert or replace one final invocation audit record."""

        async with self._session_factory() as session:
            row = await session.get(AgentInvocationRow, record.invocation_id)
            values = self._row_values(record)
            if row is None:
                session.add(AgentInvocationRow(**values))
            else:
                for field_name, value in values.items():
                    setattr(row, field_name, value)
            await session.commit()

    async def get(self, *, invocation_id: str) -> AgentInvocationRecord | None:
        """Return one invocation audit record by identifier."""

        async with self._session_factory() as session:
            row = await session.get(AgentInvocationRow, invocation_id)
            return None if row is None else self._record_from_row(row)

    @staticmethod
    def _row_values(record: AgentInvocationRecord) -> dict[str, object]:
        """Map the domain record into SQL row values."""

        return {
            "invocation_id": record.invocation_id,
            "trace_id": record.trace_id,
            "agent_name": record.agent_name,
            "prompt_version": record.prompt_version,
            "contract_version": record.contract_version,
            "provider": record.provider,
            "model": record.model,
            "status": record.status.value,
            "validation_status": record.validation_status.value,
            "latency_ms": record.latency_ms,
            "confidence": record.confidence,
            "cost_metadata_json": record.cost_metadata,
            "input_fields_json": record.input_fields,
            "output_fields_json": record.output_fields,
            "error_code": record.error_code,
            "error_message": record.error_message,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
        }

    @staticmethod
    def _record_from_row(row: AgentInvocationRow) -> AgentInvocationRecord:
        """Map one SQL row into the domain audit record."""

        return AgentInvocationRecord(
            invocation_id=row.invocation_id,
            trace_id=row.trace_id,
            agent_name=row.agent_name,
            prompt_version=row.prompt_version,
            contract_version=row.contract_version,
            provider=row.provider,
            model=row.model,
            status=row.status,
            validation_status=row.validation_status,
            latency_ms=row.latency_ms,
            confidence=row.confidence,
            cost_metadata=dict(row.cost_metadata_json),
            input_fields=list(row.input_fields_json),
            output_fields=list(row.output_fields_json),
            error_code=row.error_code,
            error_message=row.error_message,
            started_at=SqlAgentInvocationRepository._as_utc(row.started_at),
            completed_at=SqlAgentInvocationRepository._as_utc(row.completed_at),
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Normalize timestamps returned by databases that omit timezone metadata."""

        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
