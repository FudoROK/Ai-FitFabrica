"""Pub/Sub normalized-event orchestration kept below transport entrypoint."""
from __future__ import annotations

import logging
from dataclasses import dataclass
import asyncio
import socket
from typing import Awaitable, Callable

from src.adapters.database.firestore.event_state_machine import (
    complete_normalized_event_processing,
    fail_normalized_event_processing,
    processing_renew_interval_seconds,
    renew_normalized_event_processing_lease,
    start_normalized_event_processing,
)
from .policies import normalize_idempotency_key_parts

pubsub_logger = logging.getLogger("pubsub_push")


@dataclass(frozen=True)
class PubSubPipelineOutcome:
    kind: str
    pipeline_status: str


async def process_pubsub_normalized_event(
    normalized: dict,
    handle_message: Callable[[dict], Awaitable[object]],
) -> PubSubPipelineOutcome:
    try:
        channel, event_identity = normalize_idempotency_key_parts(normalized.get("channel"), normalized.get("event_identity"))
        update_key = f"{channel}:{event_identity}"
        state = start_normalized_event_processing(
            update_key=update_key,
            channel=channel,
            conversation_identity=normalized.get("conversation_identity"),
            event_identity=event_identity,
            source="pubsub",
            owner=f"{socket.gethostname()}:{update_key}",
        )
    except ValueError:
        return PubSubPipelineOutcome(kind="invalid_idempotency_key", pipeline_status="failed")
    except Exception:
        return PubSubPipelineOutcome(kind="idempotency_unavailable", pipeline_status="failed")

    if state.decision == "already_completed":
        return PubSubPipelineOutcome(kind="duplicate_skipped", pipeline_status="success")
    if state.decision == "already_processing":
        return PubSubPipelineOutcome(kind="already_processing", pipeline_status="partial")
    if state.decision == "reclaimed":
        pubsub_logger.info("PUBSUB_PROCESSING_RECLAIMED", extra={"event_key": update_key})
    pubsub_logger.info("PUBSUB_START_PROCESSING", extra={"event_key": update_key, "decision": state.decision})
    owner_token = getattr(state, "owner_token", None)

    lease_lost = False
    stop_heartbeat = asyncio.Event()
    renew_interval = processing_renew_interval_seconds()

    async def _lease_heartbeat() -> None:
        nonlocal lease_lost
        while not stop_heartbeat.is_set():
            try:
                await asyncio.wait_for(stop_heartbeat.wait(), timeout=renew_interval)
                break
            except asyncio.TimeoutError:
                pass
            try:
                renewed = await asyncio.to_thread(
                        renew_normalized_event_processing_lease,
                        update_key,
                        owner_token=str(owner_token or ""),
                )
            except Exception:
                lease_lost = True
                pubsub_logger.exception("PUBSUB_LEASE_RENEWAL_FAILURE", extra={"event_key": update_key})
                return
            if not renewed:
                lease_lost = True
                pubsub_logger.error("PUBSUB_LEASE_RENEWAL_REJECTED", extra={"event_key": update_key})
                return
            pubsub_logger.info("PUBSUB_LEASE_RENEWAL_SUCCESS", extra={"event_key": update_key})

    heartbeat_task = asyncio.create_task(_lease_heartbeat())
    normalized = dict(normalized)
    normalized["_event_key"] = update_key
    normalized["_processing_token"] = owner_token

    try:
        pipeline_result = await handle_message(normalized)
        stop_heartbeat.set()
        await heartbeat_task
        if lease_lost:
            fail_normalized_event_processing(
                update_key,
                owner_token=str(owner_token or ""),
                error="lease_renewal_failed",
            )
            return PubSubPipelineOutcome(kind="dialog_failed", pipeline_status="failed")
        complete_normalized_event_processing(update_key, owner_token=str(owner_token or ""))
        pubsub_logger.info("PUBSUB_COMPLETE_PROCESSING", extra={"event_key": update_key})
    except Exception as exc:
        stop_heartbeat.set()
        await heartbeat_task
        fail_normalized_event_processing(update_key, owner_token=str(owner_token or ""), error=str(exc))
        pubsub_logger.info("PUBSUB_FAIL_PROCESSING", extra={"event_key": update_key})
        pubsub_logger.exception("DIALOG_PIPELINE_FAILED", extra={"task": "dialog_reply", "status": "failed"})
        return PubSubPipelineOutcome(kind="dialog_failed", pipeline_status="failed")

    return PubSubPipelineOutcome(kind="ok", pipeline_status=pipeline_result.status)
