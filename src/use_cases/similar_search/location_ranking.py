"""Location-first ranking helpers for Similar Search."""

from __future__ import annotations

from typing import Literal

from src.domain.similar_search import CatalogOfferRecord

LocationMatch = Literal["same_city", "same_country_delivery", "same_country", "delivery_available", "remote", "unknown"]


def classify_location_match(
    *,
    offer: CatalogOfferRecord,
    user_country_code: str | None,
    user_city: str | None,
) -> LocationMatch:
    """Classify how well one offer matches the user's location."""

    normalized_user_country = _normalize(user_country_code)
    normalized_user_city = _normalize(user_city)
    offer_country = _normalize(offer.country_code)
    offer_city = _normalize(offer.city)
    delivery_regions = {_normalize(region) for region in offer.delivery_regions}

    if not normalized_user_country and not normalized_user_city:
        return "unknown"
    same_country = bool(normalized_user_country and offer_country == normalized_user_country)
    same_city = bool(normalized_user_city and offer_city == normalized_user_city)
    delivers_to_city = bool(normalized_user_city and normalized_user_city in delivery_regions)
    if same_city:
        return "same_city"
    if same_country and delivers_to_city:
        return "same_country_delivery"
    if same_country:
        return "same_country"
    if delivers_to_city:
        return "delivery_available"
    return "remote"


def location_priority(match: LocationMatch) -> int:
    """Return descending priority for location-first sorting."""

    priorities: dict[LocationMatch, int] = {
        "same_city": 5,
        "same_country_delivery": 4,
        "same_country": 3,
        "delivery_available": 2,
        "remote": 1,
        "unknown": 0,
    }
    return priorities[match]


def location_explanation(match: LocationMatch) -> str:
    """Return a short user-facing location explanation clause."""

    explanations: dict[LocationMatch, str] = {
        "same_city": "same city",
        "same_country_delivery": "same country and delivers to your city",
        "same_country": "same country",
        "delivery_available": "delivery available to your city",
        "remote": "remote offer",
        "unknown": "location not provided",
    }
    return explanations[match]


def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold()
