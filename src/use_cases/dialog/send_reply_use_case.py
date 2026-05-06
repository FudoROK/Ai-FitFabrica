from __future__ import annotations

import logging

from ...services.runtime.step_idempotency import StepContext, StepIdempotencyPolicy
from ...services.runtime.step_keys import StepKeys

logger = logging.getLogger(__name__)


class SendReplyUseCase:
    def __init__(
        self,
        *,
        messaging,
        step_idempotency: StepIdempotencyPolicy | None = None,
    ) -> None:
        self.messaging = messaging
        self.step_idempotency = step_idempotency or StepIdempotencyPolicy()

    async def execute(
        self,
        *,
        channel: str,
        chat_id,
        reply_text: str,
        event_key: str | None,
        owner_token: str | None,
    ) -> bool:
        normalized_channel = str(channel or "").strip().lower()
        if not reply_text or not normalized_channel or chat_id is None:
            return False

        context = StepContext(event_key=event_key, owner_token=owner_token)
        step_name = StepKeys.SEND_REPLY
        step_key = self.step_idempotency.resolve_step_key(step=step_name, channel=normalized_channel)

        if self.step_idempotency.is_step_completed(step=step_name, context=context, channel=normalized_channel):
            logger.info("step_skipped_due_to_idempotency", extra={"event_key": event_key, "step_key": step_key})
            return False

        await self.messaging.send_message(chat_id, reply_text)

        marked = self.step_idempotency.mark_step_completed(
            step=step_name,
            context=context,
            channel=normalized_channel,
            metadata={"channel": normalized_channel},
        )
        if event_key and owner_token and not marked:
            logger.warning(
                "step_completion_mark_failed",
                extra={"event_key": event_key, "step_key": step_key},
            )

        return True
