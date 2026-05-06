"""DialogService thin façade over assembled ingress and orchestration roles."""
from __future__ import annotations

from typing import Optional

from src.domain.pipeline_status import PipelineResult
from src.llm import LLMService
from .dialog_orchestrator import DialogOrchestrator
from .dialog_pipeline_assembler import DialogPipelineAssembler
from ..runtime.feature_flags import resolve_feature_flags
from src.domain.contracts.persistence import LeadRepositoryPort, SessionRepositoryPort
from src.identity_core.services.identity_core_runtime_repositories import (
    FirestoreChannelIdentityRepository,
    FirestoreIdentityBindingRepository,
    FirestoreLeadIdentityRepository,
    InMemoryChannelIdentityRepository,
    InMemoryIdentityBindingRepository,
    InMemoryLeadIdentityRepository,
)
from src.identity_core.services.identity_resolution import RuntimeIdentityResolutionService
from ..inbound.inbound_gate_service import InboundGateService
from src.services.rate_limit import RateLimiter


class DialogService:
    """Backward-compatible runtime façade for dialog pipeline."""

    def __init__(
        self,
        messaging,
        leads_repo: Optional[LeadRepositoryPort] = None,
        sessions_repo: Optional[SessionRepositoryPort] = None,
        *,
        settings=None,
        rate_limiter: RateLimiter | None = None,
        llm_service: LLMService | None = None,
        identity_resolution_service: RuntimeIdentityResolutionService | None = None,
    ) -> None:
        self.messaging = messaging
        components = DialogPipelineAssembler(
            messaging=messaging,
            leads_repo=leads_repo,
            sessions_repo=sessions_repo,
            settings=settings,
            rate_limiter=rate_limiter,
            llm_service=llm_service,
        ).assemble()

        self.settings = components.settings
        self.leads_repo = components.leads_repo
        self.sessions_repo = components.sessions_repo
        self.llm_service = components.llm_service
        self.rate_limiter = components.rate_limiter

        self.identity_resolution_service = identity_resolution_service or self._build_identity_resolution_service()

        self.inbound_gate_service = InboundGateService(
            leads_repo=self.leads_repo,
            sessions_repo=self.sessions_repo,
            rate_limiter=self.rate_limiter,
            identity_resolution_service=self.identity_resolution_service,
        )
        self.dialog_orchestrator = DialogOrchestrator(
            handle_inbound_message_use_case=components.handle_inbound_message_use_case,
            feature_flags=resolve_feature_flags(self.settings),
        )

    def _build_identity_resolution_service(self) -> RuntimeIdentityResolutionService:
        if self._is_test_environment():
            return RuntimeIdentityResolutionService(
                channel_identity_repo=InMemoryChannelIdentityRepository(),
                identity_binding_repo=InMemoryIdentityBindingRepository(),
                lead_repo=InMemoryLeadIdentityRepository(),
            )

        return RuntimeIdentityResolutionService(
            channel_identity_repo=FirestoreChannelIdentityRepository(),
            identity_binding_repo=FirestoreIdentityBindingRepository(),
            lead_repo=FirestoreLeadIdentityRepository(),
        )

    def _is_test_environment(self) -> bool:
        return str(getattr(self.settings, "environment", "")).strip().lower() == "test"

    async def handle_normalized_message(self, message: dict) -> PipelineResult:
        return await self.handle_inbound_event(message)

    async def handle_inbound_event(self, message: dict) -> PipelineResult:
        gate_decision = await self.inbound_gate_service.prepare(message)
        if gate_decision.terminal_result is not None:
            return gate_decision.terminal_result
        if gate_decision.lead is None or gate_decision.session is None:
            raise RuntimeError("Inbound gate must return lead/session when terminal_result is not set")
        return await self.dialog_orchestrator.execute(
            message=message,
            lead=gate_decision.lead,
            session=gate_decision.session,
        )
