"""Async-facing Firestore repository facades."""

from .firestore_lead_repository_facade import FirestoreLeadRepository as _FirestoreLeadRepositoryBase
from .firestore_session_repository import FirestoreSessionRepository as _FirestoreSessionRepositoryBase


class FirestoreLeadRepository(_FirestoreLeadRepositoryBase):
    """Compatibility wrapper over the split lead repository facade."""

    # Canonical lead patch normalization still happens in the lead facade via
    # patch_preparation_service.compose(...).
    pass


class FirestoreSessionRepository(_FirestoreSessionRepositoryBase):
    """Compatibility wrapper over the split session repository facade."""

    pass

__all__ = [
    "FirestoreLeadRepository",
    "FirestoreSessionRepository",
]
