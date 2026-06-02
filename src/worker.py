"""Portable worker process entrypoint for queued workflow execution."""

from __future__ import annotations

import asyncio
import logging
import signal

from src.entrypoints.runtime_dependencies import operations_runtime_dependencies
from src.settings import load_settings

logger = logging.getLogger(__name__)


async def run_worker_forever() -> int:
    """Run the portable worker loop until the process receives a shutdown signal."""
    settings = load_settings()
    runtime = operations_runtime_dependencies(settings).worker_runtime
    poll_interval_seconds = float(getattr(settings, "operations_worker_poll_interval_seconds", 1.0))
    stop_event = asyncio.Event()
    _install_signal_handlers(stop_event)

    logger.info(
        "Starting portable worker loop.",
        extra={
            "worker_name": getattr(settings, "operations_worker_name", "portable-worker"),
            "queue_backend": getattr(settings, "operations_queue_backend", "in_memory"),
            "poll_interval_seconds": poll_interval_seconds,
        },
    )

    while not stop_event.is_set():
        result = await runtime.run_one_cycle()
        if result.claimed_job_id is None:
            await asyncio.wait_for(_wait_for_stop(stop_event), timeout=poll_interval_seconds)
            continue

        logger.info(
            "Worker cycle completed.",
            extra={
                "claimed_job_id": result.claimed_job_id,
                "completed_jobs": result.completed_jobs,
                "failed_jobs": result.failed_jobs,
                "skipped_jobs": result.skipped_jobs,
            },
        )
    logger.info("Portable worker loop stopped.")
    return 0


async def _wait_for_stop(stop_event: asyncio.Event) -> None:
    """Wait until a stop signal arrives."""
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        return


def _install_signal_handlers(stop_event: asyncio.Event) -> None:
    """Install best-effort signal handlers for graceful container shutdown."""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            signal.signal(sig, lambda _signum, _frame: stop_event.set())


def main() -> int:
    """Run the worker entrypoint from a process-oriented CLI context."""
    return asyncio.run(run_worker_forever())


if __name__ == "__main__":
    raise SystemExit(main())
