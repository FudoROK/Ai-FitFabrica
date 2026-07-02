"""Provider-neutral contracts for backend-owned agent invocations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

_FORBIDDEN_AGENT_INPUT_KEYWORDS = (
    "authorization",
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "private_key",
    "cookie",
)


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class StrictAgentRuntimeModel(BaseModel):
    """Base model that rejects undeclared agent-runtime fields."""

    model_config = ConfigDict(extra="forbid")


class AgentRuntimeStatus(str, Enum):
    """Final status of one backend-owned agent invocation."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AgentValidationStatus(str, Enum):
    """Backend validation status for an agent provider output."""

    NOT_RUN = "not_run"
    PASSED = "passed"
    FAILED = "failed"


class AgentProviderFailure(RuntimeError):
    """Typed safe failure raised by the canonical provider gateway."""

    def __init__(self, *, code: str, message: str, retriable: bool) -> None:
        """Store safe provider failure metadata for backend mapping."""

        super().__init__(message)
        self.code = code
        self.message = message
        self.retriable = retriable


class AgentArtifactReference(StrictAgentRuntimeModel):
    """Approved durable artifact reference that an agent may inspect."""

    purpose: str = Field(min_length=1, max_length=128)
    object_key: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class AgentInvocationRequest(StrictAgentRuntimeModel):
    """Backend-approved request sent through the canonical agent gateway."""

    invocation_id: str = Field(default_factory=lambda: f"agent_invocation_{uuid4().hex}", min_length=1)
    agent_name: str = Field(min_length=1, max_length=128)
    prompt_version: str = Field(min_length=1, max_length=128)
    contract_version: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1)
    input_payload: dict[str, object] = Field(default_factory=dict)
    artifact_references: list[AgentArtifactReference] = Field(default_factory=list, max_length=8)
    response_schema: dict[str, object]
    timeout_seconds: float = Field(default=120.0, gt=0.0, le=300.0)
    preferred_model: str | None = Field(default=None, max_length=255)
    workflow_type: str | None = Field(default=None, min_length=1, max_length=128)
    attempt_number: int = Field(default=1, ge=1)
    retry_reason: str | None = Field(default=None, min_length=1, max_length=128)
    repair_reason: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("input_payload", mode="before")
    @classmethod
    def validate_approved_context(cls, value: object) -> object:
        """Reject secrets and binary artifacts before they can reach an agent."""

        cls._validate_context_value(value)
        return value

    @classmethod
    def _validate_context_value(cls, value: object, *, key_hint: str | None = None) -> None:
        """Recursively validate that agent context is safe JSON-style metadata."""

        normalized_key = str(key_hint or "").strip().lower().replace("-", "_")
        if any(keyword in normalized_key for keyword in _FORBIDDEN_AGENT_INPUT_KEYWORDS):
            raise ValueError(f"agent input field is forbidden: {key_hint}")
        if isinstance(value, (bytes, bytearray, memoryview)):
            raise ValueError("binary agent input is forbidden; pass an approved artifact reference")
        if isinstance(value, Mapping):
            for item_key, item_value in value.items():
                cls._validate_context_value(item_value, key_hint=str(item_key))
            return
        if isinstance(value, Sequence) and not isinstance(value, str):
            for item in value:
                cls._validate_context_value(item, key_hint=key_hint)


class AgentProviderResult(StrictAgentRuntimeModel):
    """Structured provider result returned to the invocation service."""

    payload: dict[str, object]
    provider: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=255)
    latency_ms: int = Field(ge=0)
    cost_metadata: dict[str, object] = Field(default_factory=dict)


class AgentInvocationErrorDetail(StrictAgentRuntimeModel):
    """Safe typed error exposed to backend workflows."""

    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)
    retriable: bool = False


class AgentInvocationEnvelope(StrictAgentRuntimeModel):
    """Validated result envelope consumed by backend workflows."""

    invocation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    agent_name: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    status: AgentRuntimeStatus
    validation_status: AgentValidationStatus
    output: dict[str, object] | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    cost_metadata: dict[str, object] = Field(default_factory=dict)
    error: AgentInvocationErrorDetail | None = None


class AgentInvocationRecord(StrictAgentRuntimeModel):
    """Safe durable audit record for one agent invocation."""

    invocation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    agent_name: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    status: AgentRuntimeStatus
    validation_status: AgentValidationStatus
    latency_ms: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    cost_metadata: dict[str, object] = Field(default_factory=dict)
    input_fields: list[str] = Field(default_factory=list)
    output_fields: list[str] = Field(default_factory=list)
    error_code: str | None = Field(default=None, max_length=64)
    error_message: str | None = Field(default=None, max_length=500)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime = Field(default_factory=utc_now)
