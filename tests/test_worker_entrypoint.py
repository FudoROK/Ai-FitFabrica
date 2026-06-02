from __future__ import annotations

from types import SimpleNamespace

import pytest

from src import worker


@pytest.mark.asyncio
async def test_run_worker_forever_processes_one_job_cycle_and_stops(monkeypatch) -> None:
    stop_event = None

    class _Runtime:
        def __init__(self) -> None:
            self.calls = 0

        async def run_one_cycle(self):
            self.calls += 1
            if self.calls == 1:
                assert stop_event is not None
                stop_event.set()
                return SimpleNamespace(claimed_job_id="queue-job-1", completed_jobs=1, failed_jobs=0, skipped_jobs=0)
            raise AssertionError("worker loop should have stopped after the first cycle")

    fake_runtime = _Runtime()

    def _install(stop):
        nonlocal stop_event
        stop_event = stop

    monkeypatch.setattr(
        worker,
        "load_settings",
        lambda: SimpleNamespace(operations_worker_poll_interval_seconds=1.0, operations_worker_name="portable-worker", operations_queue_backend="redis"),
    )
    monkeypatch.setattr(
        worker,
        "operations_runtime_dependencies",
        lambda _settings: SimpleNamespace(worker_runtime=fake_runtime),
    )
    monkeypatch.setattr(worker, "_install_signal_handlers", _install)

    exit_code = await worker.run_worker_forever()

    assert stop_event is not None
    assert exit_code == 0
    assert fake_runtime.calls == 1
