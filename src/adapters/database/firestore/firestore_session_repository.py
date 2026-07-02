"""Async-facing Firestore chat-session facade."""
from __future__ import annotations

from typing import Optional

from src.domain.models import ChatSession

from .firestore_async_executor import run_blocking
from .storage_primitives import get_or_create_chat_session, update_chat_session


class FirestoreSessionRepository:
    """Persist chat sessions in Firestore only."""

    async def get_or_create(
        self,
        *,
        channel: str,
        chat_id: str | int | None,
        external_user_id: str | int | None,
        lead_id: Optional[str],
    ) -> ChatSession:
        firestore_session = await run_blocking(
            get_or_create_chat_session,
            channel,
            str(external_user_id or chat_id),
            username=None,
        )
        if not firestore_session:
            raise RuntimeError("Firestore is unavailable: failed to get or create chat session")
        firestore_session.lead_id = lead_id or firestore_session.lead_id
        firestore_session.chat_id = str(chat_id) if chat_id is not None else firestore_session.chat_id
        firestore_session.channel = firestore_session.channel or channel
        firestore_session.external_user_id = firestore_session.external_user_id or str(external_user_id or chat_id)
        return firestore_session

    async def get(self, session_id: str) -> Optional[ChatSession]:
        if not session_id or ":" not in session_id:
            return None
        channel, external_user_id = session_id.split(":", 1)
        session = await run_blocking(get_or_create_chat_session, channel, external_user_id, username=None)
        if not session:
            raise RuntimeError("Firestore is unavailable: failed to fetch chat session")
        return session

    async def save(self, session: ChatSession) -> None:
        if not session or not session.id:
            return
        await run_blocking(update_chat_session, session)
