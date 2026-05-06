"""Firestore-backed distributed fixed-window rate limiter."""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from .contracts import RateLimitDecision, TransactionRunner


class FirestoreRateLimiter:
    def __init__(
        self,
        *,
        firestore_client: Any,
        max_events: int,
        window_seconds: int,
        collection_name: str = "runtime_rate_limits",
        transaction_runner: TransactionRunner | None = None,
    ) -> None:
        if firestore_client is None:
            raise RuntimeError("Firestore client is required for FirestoreRateLimiter")
        if max_events <= 0:
            raise ValueError("max_events must be > 0")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

        self._client = firestore_client
        self.max_events = max_events
        self.window_seconds = window_seconds
        self.collection_name = collection_name
        self._transaction_runner = transaction_runner

    def allow(self, key: str) -> RateLimitDecision:
        if not key:
            key = "unknown"

        doc_ref = self._client.collection(self.collection_name).document(self._doc_id(key))
        def _work(txn: Any) -> RateLimitDecision:
            now = datetime.now(timezone.utc)

            snapshot = doc_ref.get(transaction=txn)
            payload = (
                snapshot.to_dict()
                if snapshot is not None and getattr(snapshot, "exists", False)
                else {}
            )

            window_start = self._coerce_utc(payload.get("window_start"))
            count = int(payload.get("count", 0) or 0)

            window_delta = timedelta(seconds=self.window_seconds)

            if window_start is None or now >= window_start + window_delta:
                window_start = now
                count = 0

            expire_at = window_start + timedelta(seconds=self.window_seconds * 2)

            if count >= self.max_events:
                retry_after = max(
                    math.ceil((window_start + window_delta - now).total_seconds()),
                    1,
                )
                txn.set(
                    doc_ref,
                    {
                        "key": key,
                        "window_start": window_start,
                        "count": count,
                        "updated_at": now,
                        "expire_at": expire_at,
                    },
                    merge=True,
                )
                return RateLimitDecision(
                    status="denied_limit_exceeded",
                    remaining=0,
                    retry_after_seconds=retry_after,
                    reason="rate_limit_exceeded",
                )

            new_count = count + 1
            txn.set(
                doc_ref,
                {
                    "key": key,
                    "window_start": window_start,
                    "count": new_count,
                    "updated_at": now,
                    "expire_at": expire_at,
                },
                merge=True,
            )
            return RateLimitDecision(
                status="allowed",
                remaining=max(self.max_events - new_count, 0),
                retry_after_seconds=None,
                reason=None,
            )

        if self._transaction_runner is None:
            raise RuntimeError("Firestore transaction runner is required for FirestoreRateLimiter")
        return self._transaction_runner(self._client, _work)

    @staticmethod
    def _doc_id(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _coerce_utc(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return None
