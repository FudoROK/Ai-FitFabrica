"""Shared domain models for backend-owned media references."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.try_on import utc_now


class MediaObjectRef(BaseModel):
    """Portable reference to a stored binary object."""

    model_config = ConfigDict(extra="forbid")

    storage_backend: Literal["in_memory", "s3"]
    bucket_name: str | None = None
    object_key: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("sha256")
    @classmethod
    def _validate_sha256_hex(cls, value: str) -> str:
        """Require a full SHA-256 digest encoded as 64 hexadecimal characters."""
        if not all(char in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("sha256 must be 64 hexadecimal characters")
        return value
