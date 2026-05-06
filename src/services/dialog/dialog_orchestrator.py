"""Dialog orchestration handoff to inbound use-case."""
from __future__ import annotations

import logging

from src.domain.models import ChatSession, Lead
from src.domain.pipeline_status import PipelineResult
from ..runtime.feature_flags import FeatureFlags, resolve_feature_flags
from src.use_cases.dialog import HandleInboundMessageUseCase

logger = logging.getLogger(__name__)


class DialogOrchestrator:
    """Executes dialog orchestration once ingress context is prepared."""

    def __init__(
        self,
        *,
        handle_inbound_message_use_case: HandleInboundMessageUseCase,
        feature_flags: FeatureFlags | None = None,
    ) -> None:
        self._handle_inbound_message_use_case = handle_inbound_message_use_case
        self._feature_flags = feature_flags or resolve_feature_flags()

    async def execute(self, *, message: dict, lead: Lead, session: ChatSession) -> PipelineResult:
        logger.info(
            "dialog_profile_runtime_routing",
            extra={
                "profile_runtime_enabled": self._feature_flags.reply_runtime_enabled(),
                "memory_profile_runtime_enabled": self._feature_flags.memory_runtime_enabled(),
            },
        )
        return await self._handle_inbound_message_use_case.execute(message=message, lead=lead, session=session)
