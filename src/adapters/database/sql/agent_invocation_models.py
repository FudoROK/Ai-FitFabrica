"""Portable SQLAlchemy model for the agent invocation audit ledger."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class AgentInvocationRow(SqlBase):
    """Safe agent invocation audit row without raw prompts or payloads."""

    __tablename__ = "agent_invocations"

    invocation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    prompt_version: Mapped[str] = mapped_column(String(128), nullable=False)
    contract_version: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_metadata_json: Mapped[dict[str, object]] = mapped_column("cost_metadata", JSON, nullable=False, default=dict)
    input_fields_json: Mapped[list[str]] = mapped_column("input_fields", JSON, nullable=False, default=list)
    output_fields_json: Mapped[list[str]] = mapped_column("output_fields", JSON, nullable=False, default=list)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_agent_invocations_agent_started_at", AgentInvocationRow.agent_name, AgentInvocationRow.started_at)

