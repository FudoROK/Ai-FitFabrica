from __future__ import annotations

import unicodedata
from typing import Optional
from zoneinfo import ZoneInfo

from .models import TimezoneResolutionInput, TimezoneResolutionResult

_COUNTRY_ALIASES: dict[str, str] = {
    "usa": "united states",
    "us": "united states",
    "u.s.": "united states",
    "u.s.a.": "united states",
    "uk": "united kingdom",
    "uae": "united arab emirates",
    "россия": "russia",
    "рф": "russia",
    "казахстан": "kazakhstan",
    "германия": "germany",
    "сша": "united states",
    "великобритания": "united kingdom",
}

_CITY_ALIASES: dict[str, str] = {
    "москва": "moscow",
    "алматы": "almaty",
    "берлин": "berlin",
    "нью йорк": "new york",
    "нью-йорк": "new york",
    "лондон": "london",
    "париж": "paris",
}

CITY_COUNTRY_TIMEZONE_REGISTRY: dict[tuple[str, str], str] = {
    ("moscow", "russia"): "Europe/Moscow",
    ("almaty", "kazakhstan"): "Asia/Almaty",
    ("new york", "united states"): "America/New_York",
    ("los angeles", "united states"): "America/Los_Angeles",
    ("chicago", "united states"): "America/Chicago",
    ("miami", "united states"): "America/New_York",
    ("london", "united kingdom"): "Europe/London",
    ("berlin", "germany"): "Europe/Berlin",
    ("paris", "france"): "Europe/Paris",
    ("madrid", "spain"): "Europe/Madrid",
    ("rome", "italy"): "Europe/Rome",
    ("lisbon", "portugal"): "Europe/Lisbon",
    ("warsaw", "poland"): "Europe/Warsaw",
    ("kyiv", "ukraine"): "Europe/Kyiv",
    ("kiev", "ukraine"): "Europe/Kyiv",
    ("istanbul", "turkey"): "Europe/Istanbul",
    ("dubai", "united arab emirates"): "Asia/Dubai",
    ("riyadh", "saudi arabia"): "Asia/Riyadh",
    ("doha", "qatar"): "Asia/Qatar",
    ("delhi", "india"): "Asia/Kolkata",
    ("mumbai", "india"): "Asia/Kolkata",
    ("bangalore", "india"): "Asia/Kolkata",
    ("bengaluru", "india"): "Asia/Kolkata",
    ("singapore", "singapore"): "Asia/Singapore",
    ("tokyo", "japan"): "Asia/Tokyo",
    ("seoul", "south korea"): "Asia/Seoul",
    ("sydney", "australia"): "Australia/Sydney",
    ("melbourne", "australia"): "Australia/Melbourne",
    ("toronto", "canada"): "America/Toronto",
    ("vancouver", "canada"): "America/Vancouver",
    ("mexico city", "mexico"): "America/Mexico_City",
    ("sao paulo", "brazil"): "America/Sao_Paulo",
    ("rio de janeiro", "brazil"): "America/Sao_Paulo",
    ("buenos aires", "argentina"): "America/Argentina/Buenos_Aires",
    ("johannesburg", "south africa"): "Africa/Johannesburg",
    ("cairo", "egypt"): "Africa/Cairo",
    ("lagos", "nigeria"): "Africa/Lagos",
}


def _normalize_token(value: Optional[str]) -> Optional[str]:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.strip().split())
    if not compact:
        return None
    normalized = unicodedata.normalize("NFKC", compact).casefold()
    return normalized


def _normalize_city(city: Optional[str]) -> Optional[str]:
    normalized = _normalize_token(city)
    if not normalized:
        return None
    return _CITY_ALIASES.get(normalized, normalized)


def _normalize_country(country: Optional[str]) -> Optional[str]:
    normalized = _normalize_token(country)
    if not normalized:
        return None
    return _COUNTRY_ALIASES.get(normalized, normalized)


class DeterministicTimezoneResolver:
    """Pure resolver for city/country -> timezone with strict deterministic policy."""

    def resolve(self, resolution_input: TimezoneResolutionInput) -> TimezoneResolutionResult:
        explicit_timezone = _normalize_token(resolution_input.timezone)
        if explicit_timezone and _is_valid_iana_timezone(resolution_input.timezone):
            return TimezoneResolutionResult(
                resolved=True,
                timezone=str(resolution_input.timezone).strip(),
                source="user_explicit",
                confidence=1.0,
                reason="explicit_timezone_accepted",
            )

        normalized_city = _normalize_city(resolution_input.city)
        normalized_country = _normalize_country(resolution_input.country)

        if normalized_city and normalized_country:
            timezone_name = CITY_COUNTRY_TIMEZONE_REGISTRY.get((normalized_city, normalized_country))
            if timezone_name:
                return TimezoneResolutionResult(
                    resolved=True,
                    timezone=timezone_name,
                    source="backend_resolved_from_city_country",
                    confidence=1.0,
                    reason="resolved_from_city_country",
                    normalized_city=normalized_city,
                    normalized_country=normalized_country,
                )
            return TimezoneResolutionResult(
                resolved=False,
                timezone=None,
                source="unknown",
                confidence=None,
                reason="city_country_not_found_or_ambiguous",
                normalized_city=normalized_city,
                normalized_country=normalized_country,
            )

        if normalized_city and not normalized_country:
            city_timezones = {
                timezone_name
                for (city_name, _country_name), timezone_name in CITY_COUNTRY_TIMEZONE_REGISTRY.items()
                if city_name == normalized_city
            }
            if len(city_timezones) == 1:
                return TimezoneResolutionResult(
                    resolved=True,
                    timezone=next(iter(city_timezones)),
                    source="backend_resolved_from_city_only",
                    confidence=1.0,
                    reason="resolved_from_unique_city",
                    normalized_city=normalized_city,
                    normalized_country=None,
                )
            return TimezoneResolutionResult(
                resolved=False,
                timezone=None,
                source="unknown",
                confidence=None,
                reason="city_only_ambiguous_or_unknown",
                normalized_city=normalized_city,
                normalized_country=normalized_country,
            )

        return TimezoneResolutionResult(
            resolved=False,
            timezone=None,
            source="unknown",
            confidence=None,
            reason="insufficient_location_data",
            normalized_city=normalized_city,
            normalized_country=normalized_country,
        )


def _is_valid_iana_timezone(value: Optional[str]) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if "/" not in candidate:
        return False
    try:
        ZoneInfo(candidate)
    except Exception:
        return False
    return True
