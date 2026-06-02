"""Provider-neutral request and result models owned by the backend."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class StructuredReasoningRequest(BaseModel):
    """Backend-owned request for structured reasoning providers."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    response_schema: dict[str, object]


class StructuredReasoningResult(BaseModel):
    """Typed response from a structured reasoning provider."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    payload: dict[str, object]
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)


class EmbeddingRequest(BaseModel):
    """Backend-owned request for embedding generation."""

    model_config = ConfigDict(extra="forbid")

    namespace: str = Field(min_length=1)
    input_text: str = Field(min_length=1)


class EmbeddingResult(BaseModel):
    """Typed embedding result returned by an embedding provider."""

    model_config = ConfigDict(extra="forbid")

    namespace: str = Field(min_length=1)
    embedding: list[float] = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)


class ImageGenerationRequest(BaseModel):
    """Backend-owned request for image generation."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    output_mime_type: str = Field(min_length=1)


class ImageGenerationResult(BaseModel):
    """Typed placeholder or real artifact reference produced by image generation."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    output_object_key: str = Field(min_length=1)
    output_mime_type: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=_utc_now)


class ImageEditingRequest(BaseModel):
    """Backend-owned request for image editing providers."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    source_object_key: str = Field(min_length=1)
    reference_object_keys: list[str] = Field(default_factory=list)
    output_mime_type: str = Field(min_length=1)


class ImageEditingResult(BaseModel):
    """Typed edited-artifact reference returned by an image editing provider."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    source_object_key: str = Field(min_length=1)
    output_object_key: str = Field(min_length=1)
    output_mime_type: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=_utc_now)
