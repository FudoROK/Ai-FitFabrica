from __future__ import annotations

from typing import Any, Optional

from src.domain.contracts.messaging import MessagingContract


class NoMessagingAdapter(MessagingContract):
    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> Optional[str]:
        return None

    async def edit_message(self, chat_id: int | str, message_id: str, text: str, **kwargs: Any) -> bool:
        return False

    async def send_buttons(self, chat_id: int | str, text: str, buttons: list[dict[str, Any]], **kwargs: Any) -> Optional[str]:
        return None

    async def send_media(self, chat_id: int | str, media_url: str, caption: Optional[str] = None, **kwargs: Any) -> Optional[str]:
        return None
