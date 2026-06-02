"""Portable SQLAlchemy models for billing and credits persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class CreditAccountRow(SqlBase):
    """Durable credit balance row for one owner."""

    __tablename__ = "credit_accounts"
    __table_args__ = (UniqueConstraint("owner_type", "owner_id", name="uq_credit_accounts_owner"),)

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    owner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    available_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CreditLedgerEventRow(SqlBase):
    """Durable idempotent credit ledger row."""

    __tablename__ = "credit_ledger_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("credit_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    credits_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after_event: Mapped[int] = mapped_column(Integer, nullable=False)
    workflow_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    workflow_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stage_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    charge_policy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkflowPricingRuleRow(SqlBase):
    """Durable workflow pricing-rule row for backend-owned cost policy."""

    __tablename__ = "workflow_pricing_rules"

    workflow_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    base_credits: Mapped[int] = mapped_column(Integer, nullable=False)
    free_retry_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    free_repair_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


Index("ix_credit_ledger_events_account_created_at", CreditLedgerEventRow.account_id, CreditLedgerEventRow.created_at)
