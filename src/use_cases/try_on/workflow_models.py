"""Typed models for the Try-On workflow service helpers."""
from __future__ import annotations

from dataclasses import dataclass

from src.domain.try_on import TryOnError, TryOnInputMetadata


@dataclass(frozen=True)
class TryOnUploadValidationConfig:
    """Validation limits for user-uploaded Try-On sandbox files."""

    allowed_content_types: set[str]
    max_upload_bytes: int


@dataclass(frozen=True)
class ValidatedTryOnUpload:
    """Validated upload bytes and sanitized metadata for one Try-On input."""

    metadata: TryOnInputMetadata
    payload: bytes


class TryOnValidationError(Exception):
    """Exception carrying a structured Try-On validation error."""

    def __init__(self, error: TryOnError) -> None:
        """Create an exception safe to map into an API error response."""
        super().__init__(error.message)
        self.error = error
