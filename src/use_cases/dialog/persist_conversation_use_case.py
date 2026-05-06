from __future__ import annotations

from datetime import datetime, timezone


class PersistConversationUseCase:
    def __init__(self, leads_repo, sessions_repo, *, memory_layer=None) -> None:
        self.leads_repo = leads_repo
        self.sessions_repo = sessions_repo
        self.memory_layer = memory_layer

    async def execute(
        self,
        *,
        lead,
        session,
        channel: str,
        chat_id,
        external_user_id,
        user_text: str,
        reply_text: str,
        event_key: str | None = None,
    ) -> None:
        await self.leads_repo.save(lead)
        await self.sessions_repo.save(session)

        now = datetime.now(tz=timezone.utc)
        user_message_id = None
        assistant_message_id = None
        if lead.lead_id:
            await self.leads_repo.update_last_activity(lead.lead_id, now)
        if lead.lead_id and user_text:
            user_message_id = await self.leads_repo.append_message(
                lead_id=lead.lead_id,
                role="user",
                text=user_text,
                timestamp=now,
                channel=channel,
                chat_id=str(chat_id) if chat_id is not None else None,
                external_user_id=str(external_user_id) if external_user_id is not None else None,
                message_idempotency_key=f"{event_key}:message:user" if event_key else None,
            )
        if lead.lead_id and reply_text:
            assistant_message_id = await self.leads_repo.append_message(
                lead_id=lead.lead_id,
                role="assistant",
                text=reply_text,
                timestamp=now,
                channel=channel,
                chat_id=str(chat_id) if chat_id is not None else None,
                external_user_id=str(external_user_id) if external_user_id is not None else None,
                message_idempotency_key=f"{event_key}:message:assistant" if event_key else None,
            )
        if self.memory_layer is not None:
            await self.memory_layer.observe_turn(
                lead=lead,
                session=session,
                user_text=user_text,
                reply_text=reply_text,
                occurred_at=now,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
            )
