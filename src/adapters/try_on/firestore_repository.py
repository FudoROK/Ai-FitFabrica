"""Firestore repository adapter for Try-On jobs."""
from __future__ import annotations

import logging
from typing import Protocol

from anyio import to_thread
from google.cloud import firestore

from src.domain.try_on import TryOnJob
from src.use_cases.try_on.ports import TryOnJobRepositoryPort
from src.use_cases.try_on.storage_errors import TryOnStorageError

logger = logging.getLogger(__name__)


class FirestoreSnapshot(Protocol):
    """Subset of Firestore document snapshot used by this adapter."""

    exists: bool

    def to_dict(self) -> dict[str, object] | None:
        """Return document data."""
        ...


class FirestoreDocument(Protocol):
    """Subset of Firestore document reference used by this adapter."""

    def set(self, data: dict[str, object]) -> None:
        """Write document data."""
        ...

    def get(self) -> FirestoreSnapshot:
        """Read document data."""
        ...


class FirestoreCollection(Protocol):
    """Subset of Firestore collection reference used by this adapter."""

    def document(self, document_id: str) -> FirestoreDocument:
        """Return a document reference."""
        ...


class FirestoreTryOnJobRepository(TryOnJobRepositoryPort):
    """Persist Try-On jobs as strict JSON-compatible Firestore documents."""

    def __init__(self, collection: FirestoreCollection) -> None:
        """Create a Firestore repository from a collection reference."""
        self._collection = collection

    @classmethod
    def from_collection_name(cls, collection_name: str) -> "FirestoreTryOnJobRepository":
        """Create the repository from a configured collection name."""
        client = firestore.Client()
        return cls(collection=client.collection(collection_name))

    async def save(self, job: TryOnJob) -> None:
        """Save a Try-On job document."""
        document = self._collection.document(job.job_id)
        try:
            await to_thread.run_sync(document.set, job.model_dump(mode="json"))
        except Exception as exc:
            logger.exception(
                "Try-On Firestore save failed.",
                extra={"try_on_storage_backend": "firestore", "try_on_storage_operation": "save_job"},
            )
            raise TryOnStorageError(
                backend="firestore",
                operation="save_job",
                public_message="Try-On job storage is temporarily unavailable.",
            ) from exc

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a Try-On job by ID, or None when it does not exist."""
        document = self._collection.document(job_id)
        try:
            snapshot = await to_thread.run_sync(document.get)
        except Exception as exc:
            logger.exception(
                "Try-On Firestore read failed.",
                extra={"try_on_storage_backend": "firestore", "try_on_storage_operation": "get_job"},
            )
            raise TryOnStorageError(
                backend="firestore",
                operation="get_job",
                public_message="Try-On job storage is temporarily unavailable.",
            ) from exc
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        if data is None:
            return None
        return TryOnJob.model_validate(data)
