"""Typed storage exceptions for the Try-On workflow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.domain.try_on import TryOnError, TryOnErrorCode


TryOnStorageBackend = Literal["gcs", "firestore"]
TryOnStorageOperation = Literal["save_upload", "save_job", "get_job"]


@dataclass
class TryOnStorageError(Exception):
    """Public-safe exception raised when a Try-On storage adapter fails."""

    backend: TryOnStorageBackend
    operation: TryOnStorageOperation
    public_message: str

    def __post_init__(self) -> None:
        """Initialize the exception message without exposing provider internals."""
        Exception.__init__(self, self.public_message)

    def to_try_on_error(self) -> TryOnError:
        """Convert the storage failure into the public Try-On error envelope."""
        return TryOnError(
            code=TryOnErrorCode.STORAGE_UNAVAILABLE,
            message=self.public_message,
            details={
                "backend": self.backend,
                "operation": self.operation,
            },
        )
