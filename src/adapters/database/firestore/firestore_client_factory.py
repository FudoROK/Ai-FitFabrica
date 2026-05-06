"""Firestore client lifecycle and transaction execution helpers."""
from __future__ import annotations

import logging
from typing import Any, Optional

try:  # pragma: no cover - optional dependency at runtime
    from google.api_core.exceptions import GoogleAPIError
except ImportError:  # pragma: no cover - fallback for local dev
    class GoogleAPIError(Exception):
        """Fallback exception when google.api_core is unavailable."""

        pass

try:  # pragma: no cover - optional dependency at runtime
    from google.cloud import firestore
except ImportError:  # pragma: no cover - fallback for local dev
    firestore = None  # type: ignore[assignment]

from src.settings import load_settings
from src.utils.log_redaction import redact

logger = logging.getLogger(__name__)

_firestore_client: Optional["firestore.Client"] = None  # type: ignore[name-defined]


def get_firestore_client() -> Optional["firestore.Client"]:
    """Return a singleton Firestore client instance."""

    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    if firestore is None:
        logger.error("google-cloud-firestore is not available; memory disabled")
        return None

    try:
        settings = load_settings()
        _firestore_client = firestore.Client(project=settings.gcp_project_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to initialize Firestore client: %s", redact(exc))
        _firestore_client = None
    return _firestore_client


def require_client_for_write() -> "firestore.Client":  # type: ignore[name-defined]
    client = get_firestore_client()
    if not client:
        raise RuntimeError("Firestore unavailable for write operation")
    return client


def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except GoogleAPIError as exc:  # pragma: no cover - network dependency
        logger.error("Firestore operation failed: %s", redact(exc))
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected Firestore error: %s", redact(exc))
        raise


def run_in_transaction(work):
    """Run `work(transaction)` using Firestore transactional retry semantics when available."""

    client = require_client_for_write()
    try:
        # Allow the transactional decorator to handle transaction creation and retry logic
        transaction = client.transaction()

        if firestore is not None:
            transactional_work = firestore.transactional(work)
            return safe_execute(transactional_work, transaction)

        return safe_execute(work, transaction)
    except GoogleAPIError: # pragma: no cover - network dependency
        # Re-raise GoogleAPIError to be caught by FailModeRateLimiter for backend_error status
        raise
    except Exception: # pragma: no cover - defensive
        # Re-raise other unexpected exceptions
        raise


def run_in_transaction_with_client(client: Any, work):
    """Run `work(transaction)` for an explicit Firestore client instance."""
    try:
        # Allow the transactional decorator to handle transaction creation and retry logic
        transaction = client.transaction()

        if firestore is not None:
            transactional_work = firestore.transactional(work)
            return safe_execute(transactional_work, transaction)

        return safe_execute(work, transaction)
    except GoogleAPIError: # pragma: no cover - network dependency
        # Re-raise GoogleAPIError to be caught by FailModeRateLimiter for backend_error status
        raise
    except Exception: # pragma: no cover - defensive
        # Re-raise other unexpected exceptions
        raise
