"""Ingress gate for identity/session bootstrap and rate-limiting."""
from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Optional

from src.domain.behavior import apply_initial_lead_state
from src.domain.channel_identity import build_channel_identity
from src.domain.models import ChatSession, Lead
from src.domain.pipeline_status import PipelineResult
from src.domain.contracts.persistence import LeadRepositoryPort, SessionRepositoryPort
from src.identity_core.services.identity_resolution import RuntimeIdentityResolutionService
from src.services.rate_limit import RateLimiter


@dataclass(frozen=True)
class InboundGateDecision:
    lead: Lead | None = None
    session: ChatSession | None = None
    terminal_result: PipelineResult | None = None


class InboundGateService:
    """Prepares inbound identity + state and applies rate-limit guard."""

    def __init__(
        self,
        *,
        leads_repo: LeadRepositoryPort,
        sessions_repo: SessionRepositoryPort,
        rate_limiter: RateLimiter,
        identity_resolution_service: RuntimeIdentityResolutionService,
    ) -> None:
        self._leads_repo = leads_repo
        self._sessions_repo = sessions_repo
        self._rate_limiter = rate_limiter
        self._identity_resolution_service = identity_resolution_service

    async def prepare(self, message: dict) -> InboundGateDecision:
        identity = build_channel_identity(message)
        resolution = await self._identity_resolution_service.resolve(
            channel=identity.channel,
            external_identity=identity.external_user_id,
        )
        lead, session = await self._ensure_session_and_lead(
            identity=identity,
            canonical_lead_id=resolution.canonical_lead_id,
            username=message.get("username"),
            first_name=message.get("first_name"),
        )

        rate_key = str(lead.lead_id or identity.source_identity or identity.conversation_identity or "unknown")
        rate_decision = self._rate_limiter.allow(rate_key)
        if rate_decision.status == "denied_limit_exceeded":
            return InboundGateDecision(terminal_result=PipelineResult(status="failed", error_type="rate_limited"))
        elif rate_decision.status == "backend_error":
            # Fail-open: log error but continue processing
            logger.error(
                "INBOUND_GATE_RATE_LIMIT_BACKEND_FAILURE",
                extra={
                    "rate_key": rate_key,
                    "reason": rate_decision.reason,
                    "fail_mode": "open",
                },
            )


        return InboundGateDecision(lead=lead, session=session)

    async def _ensure_session_and_lead(
        self,
        *,
        identity,
        canonical_lead_id: str,
        username: Optional[str],
        first_name: Optional[str],
    ) -> tuple[Lead, ChatSession]:
        lead = await self._leads_repo.get_or_create_canonical(
            canonical_lead_id=canonical_lead_id,
            channel=identity.channel,
            external_user_id=identity.external_user_id,
            username=username,
            first_name=first_name,
        )
        apply_initial_lead_state(lead)
        await self._leads_repo.save(lead)
        session = await self._sessions_repo.get_or_create(
            channel=identity.channel,
            chat_id=identity.conversation_identity,
            external_user_id=identity.external_user_id,
            lead_id=lead.lead_id,
        )
        return lead, session
