"""Composition root helpers for runtime service wiring."""
from __future__ import annotations

from src.adapters.database.firestore.firestore_client_factory import get_firestore_client
from src.adapters.factories import get_messaging_adapter
from src.memory_layer import (
    FirestoreMemoryLayerRepository,
    InMemoryMemoryRunLedgerRepository,
    MemoryLayerService,
)
from src.memory_layer.run_ledger_repository import FirestoreMemoryRunLedgerRepository
from src.memory_layer.services.memory_run_ledger_service import MemoryRunLedgerService
from ..services.dialog.dialog_service import DialogService
from src.adapters.database.firestore.firestore_repositories import FirestoreLeadRepository, FirestoreSessionRepository
from src.memory_layer.services.memory_summary_service import MemorySummaryResult, MemorySummaryService
from ..services.rate_limit import create_rate_limiter

_CONTAINER_ATTR = "_runtime_container"


class RuntimeContainer:
    """Runtime-scoped dependency container with explicit lazy lifecycle."""

    def __init__(self, settings):
        self.settings = settings
        self._dialog_service: DialogService | None = None
        self._memory_summary_service: MemorySummaryService | None = None
        self._ingress_rate_limiter = None
        self._ingress_global_rate_limiter = None

    def _is_test_environment(self) -> bool:
        return str(getattr(self.settings, "environment", "")).strip().lower() == "test"

    def get_dialog_service(self) -> DialogService:
        if self._dialog_service is None:
            memory_layer_service = MemoryLayerService(
                repository=FirestoreMemoryLayerRepository(),
                settings=self.settings,
            )
            self._dialog_service = DialogService(
                messaging=get_messaging_adapter(),
                leads_repo=FirestoreLeadRepository(memory_layer_service=memory_layer_service),
                sessions_repo=FirestoreSessionRepository(),
                settings=self.settings,
                rate_limiter=create_rate_limiter(self.settings),
            )
        return self._dialog_service

    def get_memory_summary_service(self) -> MemorySummaryService:
        if self._memory_summary_service is None:
            memory_layer_service = MemoryLayerService(
                repository=FirestoreMemoryLayerRepository(),
                settings=self.settings,
            )
            if self._is_test_environment():
                run_ledger_service = MemoryRunLedgerService(repository=InMemoryMemoryRunLedgerRepository())
            else:
                run_ledger_service = MemoryRunLedgerService(repository=FirestoreMemoryRunLedgerRepository())
            self._memory_summary_service = MemorySummaryService(
                firestore=get_firestore_client(),
                settings=self.settings,
                leads_repo=FirestoreLeadRepository(memory_layer_service=memory_layer_service),
                memory_layer_service=memory_layer_service,
                memory_run_ledger_service=run_ledger_service,
            )
        return self._memory_summary_service

    def get_ingress_rate_limiter(self):
        if self._is_test_environment():
            return create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_rate_limit_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=self.settings.ingress_rate_limit_collection,
                backend_override="inmemory",
            )
        if self._ingress_rate_limiter is None:
            self._ingress_rate_limiter = create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_rate_limit_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=self.settings.ingress_rate_limit_collection,
            )
        return self._ingress_rate_limiter

    def get_ingress_global_safety_limiter(self):
        if self._is_test_environment():
            return create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_global_safety_cap_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=f"{self.settings.ingress_rate_limit_collection}_global",
                backend_override="inmemory",
            )
        if self._ingress_global_rate_limiter is None:
            self._ingress_global_rate_limiter = create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_global_safety_cap_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=f"{self.settings.ingress_rate_limit_collection}_global",
            )
        return self._ingress_global_rate_limiter


def runtime_container(settings) -> RuntimeContainer:
    container = getattr(settings, _CONTAINER_ATTR, None)
    if container is None:
        container = RuntimeContainer(settings)
        setattr(settings, _CONTAINER_ATTR, container)
    return container


def dialog_service(settings) -> DialogService:
    return runtime_container(settings).get_dialog_service()


def memory_summary_service(settings) -> MemorySummaryService:
    return runtime_container(settings).get_memory_summary_service()


def ingress_rate_limiter(settings):
    return runtime_container(settings).get_ingress_rate_limiter()


def ingress_global_safety_limiter(settings):
    return runtime_container(settings).get_ingress_global_safety_limiter()


def safe_memory_summary_response(*, result: MemorySummaryResult) -> dict[str, object]:
    """Build a sanitized task/cron response without runtime diagnostic leakage."""
    pipeline_status = "failed" if result.outcome_counts.get("failed", 0) > 0 else "completed"
    return {
        "pipeline_status": pipeline_status,
        "date": result.date.isoformat(),
        "leads_processed": result.leads_processed,
        "summaries_written": result.summaries_written,
        "error_count": result.error_count,
        "has_errors": result.error_count > 0,
        "outcomes": dict(result.outcome_counts),
        "reason_codes": dict(result.reason_code_counts),
    }
