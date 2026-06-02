"""Typed domain models for backend-owned billing and credits logic."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def billing_utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp for billing records."""
    return datetime.now(timezone.utc)


class BillingOwnerType(StrEnum):
    """Supported durable credit account owner types."""

    PERSON = "person"
    BUSINESS = "business"


class BillingEventType(StrEnum):
    """Supported durable ledger event kinds."""

    CHARGE = "charge"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    GRANT = "grant"


class BillingChargePolicy(StrEnum):
    """Policy outcomes supported by the initial billing core."""

    STANDARD = "standard"
    FREE_RETRY = "free_retry"
    FREE_REPAIR = "free_repair"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class CreditAccount(BaseModel):
    """Durable credit balance for one backend-owned account."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    owner_type: BillingOwnerType
    available_credits: int = Field(ge=0)
    reserved_credits: int = Field(default=0, ge=0)


class WorkflowChargeRequest(BaseModel):
    """One backend-owned workflow charge request before policy resolution."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    owner_type: BillingOwnerType
    workflow_type: str = Field(min_length=1)
    workflow_reference: str = Field(min_length=1)
    stage_name: str = Field(min_length=1)
    requested_credits: int = Field(default=0, ge=0)
    charge_policy: BillingChargePolicy = BillingChargePolicy.STANDARD
    failure_owner: str | None = None
    recovery_kind: str | None = None


class ResolvedBillingPolicy(BaseModel):
    """Resolved workflow billing policy after backend rule evaluation."""

    model_config = ConfigDict(extra="forbid")

    charge_policy: BillingChargePolicy
    credits_to_charge: int = Field(ge=0)


class LedgerAppendRequest(BaseModel):
    """Canonical durable ledger append request."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    owner_type: BillingOwnerType
    event_type: BillingEventType
    credits_delta: int
    workflow_type: str | None = None
    workflow_reference: str | None = None
    stage_name: str | None = None
    charge_policy: BillingChargePolicy | None = None
    idempotency_key: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=billing_utc_now)


class LedgerEvent(BaseModel):
    """Durable ledger event returned by repository and API surfaces."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    owner_type: BillingOwnerType
    event_type: BillingEventType
    credits_delta: int
    balance_after_event: int = Field(ge=0)
    workflow_type: str | None = None
    workflow_reference: str | None = None
    stage_name: str | None = None
    charge_policy: BillingChargePolicy | None = None
    created_at: datetime = Field(default_factory=billing_utc_now)


class CreditLedgerResponse(BaseModel):
    """API-safe wrapper for one credit ledger history response."""

    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    owner_type: BillingOwnerType
    events: list[LedgerEvent] = Field(default_factory=list)
