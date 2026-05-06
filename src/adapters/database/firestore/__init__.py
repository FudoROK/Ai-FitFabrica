"""Firestore infrastructure modules."""

from .event_state_machine import (
    EventProcessingStartResult,
    complete_normalized_event_processing,
    fail_normalized_event_processing,
    start_normalized_event_processing,
)
from .storage_primitives import get_firestore_client

__all__ = [
    "EventProcessingStartResult",
    "complete_normalized_event_processing",
    "fail_normalized_event_processing",
    "start_normalized_event_processing",
    "get_firestore_client",
]
