from __future__ import annotations

import base64
import binascii
import json
from typing import Literal
from typing import Any

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

MAX_INGRESS_BODY_BYTES = 256 * 1024
MAX_TELEGRAM_TEXT_LENGTH = 4096
MAX_IDENTIFIER_LENGTH = 256
MAX_PUBSUB_DATA_LENGTH = 200_000


class IngressValidationError(ValueError):
    """Raised when ingress payload is malformed or violates schema."""


class IngressBodyTooLargeError(ValueError):
    """Raised when request body exceeds boundary size limits."""


class TelegramVoice(BaseModel):
    model_config = ConfigDict(extra="allow")

    file_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    duration: int | None = None
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = None


class TelegramPhotoSize(BaseModel):
    model_config = ConfigDict(extra="allow")

    file_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)


class TelegramDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    file_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    file_name: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = None


class TelegramUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int


class TelegramChat(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int


class TelegramMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    message_id: int
    date: int | float | str
    chat: TelegramChat
    from_user: TelegramUser = Field(alias="from")
    text: str | None = Field(default=None, max_length=MAX_TELEGRAM_TEXT_LENGTH)
    caption: str | None = Field(default=None, max_length=MAX_TELEGRAM_TEXT_LENGTH)
    voice: TelegramVoice | None = None
    photo: list[TelegramPhotoSize] | None = Field(default=None, min_length=1)
    document: TelegramDocument | None = None

    @model_validator(mode="after")
    def validate_supported_content(self) -> "TelegramMessage":
        if self.text is None and self.voice is None and self.photo is None and self.document is None:
            raise ValueError("unsupported_message_content")
        return self


class TelegramWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    update_id: int
    message: TelegramMessage | None = None
    edited_message: TelegramMessage | None = None

    # valid but currently unsupported update kinds (handled separately from malformed payload)
    callback_query: dict[str, Any] | None = None
    inline_query: dict[str, Any] | None = None
    channel_post: dict[str, Any] | None = None
    my_chat_member: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_known_update_kind(self) -> "TelegramWebhookRequest":
        if (
            self.message is None
            and self.edited_message is None
            and self.callback_query is None
            and self.inline_query is None
            and self.channel_post is None
            and self.my_chat_member is None
        ):
            raise ValueError("unsupported_or_missing_update_type")
        return self

    @property
    def update_kind(self) -> str:
        if self.message is not None:
            return "message"
        if self.edited_message is not None:
            return "edited_message"
        if self.callback_query is not None:
            return "callback_query"
        if self.inline_query is not None:
            return "inline_query"
        if self.channel_post is not None:
            return "channel_post"
        if self.my_chat_member is not None:
            return "my_chat_member"
        return "unknown"


class PubSubPushMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: str = Field(min_length=1, max_length=MAX_PUBSUB_DATA_LENGTH)
    attributes: dict[str, str] | None = None
    message_id: str | None = Field(default=None, alias="messageId", max_length=MAX_IDENTIFIER_LENGTH)
    publish_time: str | None = Field(default=None, alias="publishTime", max_length=64)


class PubSubPushRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: PubSubPushMessage
    subscription: str | None = Field(default=None, max_length=MAX_IDENTIFIER_LENGTH)
    delivery_attempt: int | None = Field(default=None, alias="deliveryAttempt")


class PubSubVoiceMedia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    duration: int | None = None
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = None


class PubSubPhotoSize(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)


class PubSubPhotoMedia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sizes: list[PubSubPhotoSize] = Field(min_length=1)


class PubSubDocumentMedia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    file_name: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = None


class PubSubNormalizedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str = Field(min_length=1, max_length=32)
    source_identity: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    conversation_identity: str = Field(min_length=1, max_length=MAX_IDENTIFIER_LENGTH)
    event_identity: str | int
    external_user_id: str | int | None = None
    content_type: Literal["text", "voice", "photo", "document"] = "text"
    text: str | None = Field(default=None, max_length=MAX_TELEGRAM_TEXT_LENGTH)
    timestamp: str | None = Field(default=None, max_length=64)
    username: str | None = Field(default=None, max_length=64)
    media: PubSubVoiceMedia | PubSubPhotoMedia | PubSubDocumentMedia | None = None

    @model_validator(mode="after")
    def validate_content_media_contract(self) -> "PubSubNormalizedPayload":
        if self.content_type == "text":
            if self.media is not None:
                raise ValueError("text_content_must_not_include_media")
            return self
        if self.media is None:
            raise ValueError("media_payload_required_for_non_text_content")
        if self.content_type == "voice" and not isinstance(self.media, PubSubVoiceMedia):
            raise ValueError("voice_content_requires_voice_media")
        if self.content_type == "photo" and not isinstance(self.media, PubSubPhotoMedia):
            raise ValueError("photo_content_requires_photo_media")
        if self.content_type == "document" and not isinstance(self.media, PubSubDocumentMedia):
            raise ValueError("document_content_requires_document_media")
        return self


class MemorySummaryTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_id: str | None = Field(default=None, min_length=1, max_length=MAX_IDENTIFIER_LENGTH)


async def read_request_body_with_limit(request: Request, *, max_bytes: int = MAX_INGRESS_BODY_BYTES) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            parsed_content_length = int(content_length)
        except ValueError as exc:
            raise IngressValidationError("invalid_content_length") from exc
        if parsed_content_length > max_bytes:
            raise IngressBodyTooLargeError("request_body_too_large")

    body = await request.body()
    if len(body) > max_bytes:
        raise IngressBodyTooLargeError("request_body_too_large")
    return body


def parse_json_model(body: bytes, model: type[BaseModel]) -> BaseModel:
    try:
        return model.model_validate_json(body)
    except ValidationError as exc:
        raise IngressValidationError("invalid_payload_schema") from exc
    except json.JSONDecodeError as exc:
        raise IngressValidationError("invalid_json") from exc


def decode_pubsub_payload(body: PubSubPushRequest) -> dict[str, Any]:
    try:
        decoded_bytes = base64.b64decode(body.message.data)
    except (ValueError, binascii.Error) as exc:
        raise IngressValidationError("invalid_pubsub_base64") from exc

    try:
        payload = json.loads(decoded_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngressValidationError("invalid_pubsub_message") from exc

    try:
        normalized = PubSubNormalizedPayload.model_validate(payload)
    except ValidationError as exc:
        raise IngressValidationError("invalid_pubsub_message") from exc

    return normalized.model_dump()
