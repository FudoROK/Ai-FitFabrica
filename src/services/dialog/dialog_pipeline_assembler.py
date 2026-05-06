"""Dependency assembly for the dialog pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.llm import LLMService
from src.memory_layer import (
    FirestoreMemoryLayerRepository,
    InMemoryMemoryLayerRepository,
    MemoryLayerService,
)
from src.settings import load_settings
from src.use_cases.dialog import (
    GenerateReplyUseCase,
    HandleInboundMessageUseCase,
    PersistConversationUseCase,
)
from src.use_cases.lead import IngestLeadPatchUseCase, ProcessWorkflowOutputUseCase
from ..context.core_context_builder import build_core_context
from .dialog_idempotency_wiring import build_send_reply_use_case
from ..runtime.feature_flags import resolve_feature_flags
from src.domain.contracts.persistence import LeadRepositoryPort, SessionRepositoryPort
from src.services.rate_limit import RateLimiter, create_rate_limiter


@dataclass(frozen=True)
class DialogPipelineComponents:
    """Materialized dependencies for dialog ingress + orchestration."""

    settings: object
    leads_repo: LeadRepositoryPort
    sessions_repo: SessionRepositoryPort
    llm_service: LLMService
    rate_limiter: RateLimiter
    handle_inbound_message_use_case: HandleInboundMessageUseCase


class DialogPipelineAssembler:
    """Builds dialog pipeline dependencies with production defaults."""

    def __init__(
        self,
        *,
        messaging,
        leads_repo: Optional[LeadRepositoryPort] = None,
        sessions_repo: Optional[SessionRepositoryPort] = None,
        settings=None,
        rate_limiter: RateLimiter | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self._messaging = messaging
        self._settings = settings
        self._leads_repo = leads_repo
        self._sessions_repo = sessions_repo
        self._rate_limiter = rate_limiter
        self._llm_service = llm_service

    def assemble(self) -> DialogPipelineComponents:
        settings = self._settings or load_settings()
        memory_layer_repository = (
            InMemoryMemoryLayerRepository()
            if str(getattr(settings, "environment", "")).strip().lower() == "test"
            else FirestoreMemoryLayerRepository()
        )
        memory_layer_service = MemoryLayerService(
            repository=memory_layer_repository,
            settings=settings,
        )
        leads_repo = self._leads_repo
        sessions_repo = self._sessions_repo
        if leads_repo is None or sessions_repo is None:
            raise RuntimeError("Lead/session repositories must be provided by DI container")
        llm_service = self._llm_service or LLMService()
        limiter_settings = settings if hasattr(settings, "rate_limit_backend") else load_settings()
        rate_limiter = self._rate_limiter or create_rate_limiter(limiter_settings)
        feature_flags = resolve_feature_flags(settings)

        async def build_context_with_memory(**kwargs):
            return await build_core_context(memory_layer=memory_layer_service, **kwargs)

        generate_reply_use_case = GenerateReplyUseCase(llm_service, feature_flags=feature_flags)
        persist_conversation_use_case = PersistConversationUseCase(
            leads_repo,
            sessions_repo,
            memory_layer=memory_layer_service,
        )
        ingest_lead_patch_use_case = IngestLeadPatchUseCase(leads_repo=leads_repo)
        send_reply_use_case = build_send_reply_use_case(messaging=self._messaging)
        process_lead_workflow_output_use_case = ProcessWorkflowOutputUseCase(
            ingest_lead_patch_use_case=ingest_lead_patch_use_case,
        )
        handle_inbound_message_use_case = HandleInboundMessageUseCase(
            leads_repo=leads_repo,
            llm_service=llm_service,
            build_context=build_context_with_memory,
            generate_reply_use_case=generate_reply_use_case,
            persist_conversation_use_case=persist_conversation_use_case,
            send_reply_use_case=send_reply_use_case,
            process_lead_workflow_output_use_case=process_lead_workflow_output_use_case,
        )
        return DialogPipelineComponents(
            settings=settings,
            leads_repo=leads_repo,
            sessions_repo=sessions_repo,
            llm_service=llm_service,
            rate_limiter=rate_limiter,
            handle_inbound_message_use_case=handle_inbound_message_use_case,
        )
