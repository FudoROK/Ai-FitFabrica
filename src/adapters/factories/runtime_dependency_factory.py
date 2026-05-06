from __future__ import annotations

from functools import lru_cache

from src.settings import load_settings
from src.domain.contracts import CalendarContract, CRMContract, MessagingContract
from .llm_provider_factory import select_calendar_adapter, select_crm_adapter, select_messaging_adapter


@lru_cache()
def get_crm_adapter() -> CRMContract:
    return select_crm_adapter(load_settings().crm_provider)


@lru_cache()
def get_calendar_adapter() -> CalendarContract:
    return select_calendar_adapter(load_settings().calendar_provider)


@lru_cache()
def get_messaging_adapter() -> MessagingContract:
    return select_messaging_adapter(load_settings().messaging_provider)


def reset_adapter_caches() -> None:
    get_crm_adapter.cache_clear()
    get_calendar_adapter.cache_clear()
    get_messaging_adapter.cache_clear()
