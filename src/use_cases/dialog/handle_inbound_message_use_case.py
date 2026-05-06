from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import perf_counter

from src.domain.channel_identity import build_channel_identity
from src.domain.models import ChatSession, Lead
from src.domain.pipeline_status import PipelineResult
from src.domain.agent_output.agent_semantic_payload_validator import SemanticValidationOutcome, SemanticValidationResult
from ...utils.log_redaction import hash_chat_id

logger = logging.getLogger(__name__)


class HandleInboundMessageUseCase:
    def __init__(
        self,
        *,
        leads_repo,
        llm_service,
        build_context,
        generate_reply_use_case,
        persist_conversation_use_case,
        send_reply_use_case,
        process_lead_workflow_output_use_case,
    ) -> None:
        self.leads_repo = leads_repo
        self.llm_service = llm_service
        self.build_context = build_context
        self.generate_reply_use_case = generate_reply_use_case
        self.persist_conversation_use_case = persist_conversation_use_case
        self.send_reply_use_case = send_reply_use_case
        self.process_lead_workflow_output_use_case = process_lead_workflow_output_use_case

    async def execute(self, *, message: dict, lead: Lead, session: ChatSession) -> PipelineResult:
        started = perf_counter()
        identity = build_channel_identity(message)
        text = (message.get("text") or "").strip()
        event_key = str(message.get("_event_key")) if message.get("_event_key") else None
        owner_token = str(message.get("_processing_token")) if message.get("_processing_token") else None

        self._apply_inbound_state(lead=lead, session=session, text=text)

        llm_context = await self.build_context(
            lead_id=str(lead.lead_id or ""),
            channel=identity.channel,
            external_user_id=identity.external_user_id,
            chat_id=identity.conversation_identity,
            leads_repo=self.leads_repo,
        )
        self._enrich_context_with_session_ids(llm_context=llm_context, session=session)

        llm_result, reply_text, system_payload, reply_meta = await self.generate_reply_use_case.execute(
            message=message,
            channel=identity.channel,
            lead_id=lead.lead_id,
            text=text,
            llm_context=llm_context,
        )
        self._apply_assistant_state(session=session, reply_text=reply_text, reply_meta=reply_meta)

        await self.persist_conversation_use_case.execute(
            lead=lead,
            session=session,
            channel=identity.channel,
            chat_id=identity.conversation_identity,
            external_user_id=identity.external_user_id,
            user_text=text,
            reply_text=reply_text,
            event_key=event_key,
        )

        processor = self.process_lead_workflow_output_use_case
        if hasattr(processor, "evaluate_semantics"):
            semantic_result = processor.evaluate_semantics(system_payload=system_payload)
        else:
            semantic_result = SemanticValidationResult(outcome=SemanticValidationOutcome.SEMANTIC_OK)

        if semantic_result.outcome != SemanticValidationOutcome.SEMANTIC_REJECT_HARD:
            await self.send_reply_use_case.execute(
                channel=identity.channel,
                chat_id=identity.conversation_identity,
                reply_text=reply_text,
                event_key=event_key,
                owner_token=owner_token,
            )

        raw_result = await self.process_lead_workflow_output_use_case.execute(
            system_payload=system_payload,
            lead=lead,
            external_user_id=identity.external_user_id,
            event_key=event_key,
            semantic_result=semantic_result,
        )

        if hasattr(raw_result, "side_effects_applied"):
            workflow_result = raw_result
        else:
            workflow_result = type(
                "WorkflowProcessingResultCompat",
                (),
                {"side_effects_applied": bool(raw_result)},
            )()

        if semantic_result.outcome != SemanticValidationOutcome.SEMANTIC_OK:
            logger.warning(
                "reply_sent_with_semantic_reject",
                extra={
                    "semantic_outcome": semantic_result.outcome,
                    "violation_codes": list(semantic_result.violation_codes),
                    "reply_sent": semantic_result.outcome != SemanticValidationOutcome.SEMANTIC_REJECT_HARD,
                },
            )

        pipeline_status = "success" if llm_result.ok else "degraded"
        logger.info(
            "dialog_pipeline_done",
            extra={
                "task": "dialog_reply",
                "status": pipeline_status,
                "lead_id": lead.lead_id,
                "chat_id_hash": hash_chat_id(identity.conversation_identity),
                "provider_name": getattr(self.llm_service.provider, "provider_name", "unknown"),
                "retry_count": 0,
                "latency_ms": int((perf_counter() - started) * 1000),
                "workflow_side_effects_applied": workflow_result.side_effects_applied,
            },
        )
        return PipelineResult(status=pipeline_status, reply_text=reply_text, error_type=(llm_result.error or {}).get("kind"))

    @staticmethod
    def _apply_inbound_state(*, lead: Lead, session: ChatSession, text: str) -> None:
        now = datetime.now(tz=timezone.utc)
        if text:
            session.add_message("user", text)
            session.last_user_message_at = now
        lead.last_contact_at = now

    @staticmethod
    def _enrich_context_with_session_ids(*, llm_context: dict, session: ChatSession) -> None:
        llm_context.setdefault("session", {})
        if session.id:
            llm_context["session"]["chat_session_id"] = session.id
        if session.vertex_session_id:
            llm_context["session"]["vertex_session_id"] = session.vertex_session_id

    @staticmethod
    def _apply_assistant_state(*, session: ChatSession, reply_text: str, reply_meta: dict | None) -> None:
        provider_session_id = reply_meta.get("provider_session_id") if isinstance(reply_meta, dict) else None
        if provider_session_id:
            session.vertex_session_id = str(provider_session_id)

        if reply_text:
            session.add_message("assistant", reply_text)
            session.last_bot_message_at = datetime.now(tz=timezone.utc)
