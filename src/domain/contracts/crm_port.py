from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class CRMOperationStatus(StrEnum):
    """CRM-neutral operation status values."""

    SUCCEEDED = "succeeded"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RETRYABLE_FAILURE = "retryable_failure"
    NON_RETRYABLE_FAILURE = "non_retryable_failure"


class CRMOperationRequest(BaseModel):
    """Provider-neutral CRM operation request."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(min_length=1)
    entity_ref: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)


class CRMOperationResult(BaseModel):
    """Provider-neutral CRM operation result."""

    model_config = ConfigDict(extra="forbid")

    status: CRMOperationStatus
    provider: str | None = None
    provider_reference: str | None = None
    message: str
    retryable: bool = False


class CRMPort(Protocol):
    """Domain-facing CRM boundary used by backend use cases."""

    async def execute(self, *, request: CRMOperationRequest) -> CRMOperationResult:
        """Execute a provider-neutral CRM operation."""
        ...
