"""Lazy runtime factories used by dependency wiring."""
from __future__ import annotations


def FirestoreLeadRepository(*args, **kwargs):
    """Load the Firestore lead repository only when runtime wiring requests it."""
    from src.adapters.database.firestore.firestore_repositories import FirestoreLeadRepository as _impl

    return _impl(*args, **kwargs)


def get_firestore_client(*args, **kwargs):
    """Load the Firestore client factory only when runtime wiring requests it."""
    from src.adapters.database.firestore.firestore_client_factory import get_firestore_client as _impl

    return _impl(*args, **kwargs)


def VertexVirtualTryOnClient(*args, **kwargs):
    """Load the Vertex virtual try-on client only when runtime wiring requests it."""
    from src.adapters.ai.vertex_virtual_try_on_client import VertexVirtualTryOnClient as _impl

    return _impl(*args, **kwargs)
