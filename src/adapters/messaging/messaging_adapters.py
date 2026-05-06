from __future__ import annotations

import logging
from typing import Any, Optional

from src.adapters.messaging.telegram.telegram_client import TelegramClient
from src.domain.contracts.messaging import MessagingContract

logger = logging.getLogger(__name__)


class TelegramAdapter(MessagingContract):
    def __init__(self, client: Optional[TelegramClient] = None) -> None:
        self.client = client or TelegramClient()

    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> Optional[str]:
        await self.client.send_message(chat_id, text, **kwargs)
        return None

    async def edit_message(self, chat_id: int | str, message_id: str, text: str, **kwargs: Any) -> bool:
        logger.info("TelegramAdapter edit_message skeleton", extra={"chat_id": str(chat_id), "message_id": message_id})
        return False

    async def send_buttons(self, chat_id: int | str, text: str, buttons: list[dict[str, Any]], **kwargs: Any) -> Optional[str]:
        logger.info("TelegramAdapter send_buttons skeleton", extra={"chat_id": str(chat_id), "buttons": len(buttons)})
        await self.client.send_message(chat_id, text, **kwargs)
        return None

    async def send_media(self, chat_id: int | str, media_url: str, caption: Optional[str] = None, **kwargs: Any) -> Optional[str]:
        logger.info("TelegramAdapter send_media skeleton", extra={"chat_id": str(chat_id), "has_caption": bool(caption)})
        if caption:
            await self.client.send_message(chat_id, caption, **kwargs)
        return None


class NoMessagingAdapter(MessagingContract):
    async def send_message(self, chat_id: int | str, text: str, **kwargs: Any) -> Optional[str]:
        return None

    async def edit_message(self, chat_id: int | str, message_id: str, text: str, **kwargs: Any) -> bool:
        return False

    async def send_buttons(self, chat_id: int | str, text: str, buttons: list[dict[str, Any]], **kwargs: Any) -> Optional[str]:
        return None

    async def send_media(self, chat_id: int | str, media_url: str, caption: Optional[str] = None, **kwargs: Any) -> Optional[str]:
        return None
