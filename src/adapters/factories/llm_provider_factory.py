from __future__ import annotations

from src.adapters.calendar.calendar_adapters import NoCalendarAdapter
from src.adapters.messaging.messaging_adapters import NoMessagingAdapter, TelegramAdapter
from src.domain.contracts import CalendarContract, CRMContract, MessagingContract
from src.adapters.crm.hubspot import HubSpotCRMAdapter
from src.adapters.crm.no_crm import NoCRMAdapter


def select_crm_adapter(provider: str) -> CRMContract:
    normalized = (provider or "none").strip().lower()
    if normalized == "hubspot":
        return HubSpotCRMAdapter()
    if normalized == "none":
        return NoCRMAdapter()
    raise ValueError("CRM_PROVIDER must be one of: hubspot, none")


def select_calendar_adapter(provider: str) -> CalendarContract:
    normalized = (provider or "none").strip().lower()
    if normalized == "none":
        return NoCalendarAdapter()
    raise ValueError("CALENDAR_PROVIDER must be one of: none")


def select_messaging_adapter(provider: str) -> MessagingContract:
    normalized = (provider or "none").strip().lower()
    if normalized == "telegram":
        return TelegramAdapter()
    if normalized == "none":
        return NoMessagingAdapter()
    raise ValueError("MESSAGING_PROVIDER must be one of: telegram, none")
