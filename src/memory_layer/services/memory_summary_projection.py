"""Projection helpers for the memory summary pipeline."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def build_lead_profile_payload(lead_data: dict) -> dict[str, str]:
    source_profile = lead_data.get("lead_profile") if isinstance(lead_data.get("lead_profile"), dict) else {}
    pain_points = source_profile.get("pain_points") if isinstance(source_profile.get("pain_points"), list) else []
    needs = source_profile.get("needs") if isinstance(source_profile.get("needs"), list) else []
    return {
        "first_name": lead_data.get("first_name") or source_profile.get("first_name") or "",
        "company_or_niche": lead_data.get("business_type") or lead_data.get("business_description") or source_profile.get("business_type") or source_profile.get("business_description") or "",
        "pain_points": ", ".join(str(item) for item in pain_points if item is not None),
        "need_solution": ", ".join(str(item) for item in needs if item is not None) or lead_data.get("recommended_package") or source_profile.get("recommended_package") or "",
    }


async def fetch_messages_for_window(
    *,
    leads_repo,
    lead_id: str,
    start_utc: datetime,
    end_utc: datetime,
    limit: int,
) -> list[dict]:
    raw_messages = await leads_repo.get_messages_in_window(
        lead_id=lead_id,
        start_utc=start_utc,
        end_utc=end_utc,
        limit=limit,
    )
    messages: list[dict] = []
    for data in raw_messages:
        text = data.get("text") or ""
        if not text:
            continue
        messages.append(
            {
                "role": data.get("role") or "user",
                "text": text,
                "ts": normalize_timestamp(data.get("timestamp")),
            }
        )
    return messages


def normalize_timestamp(value: Optional[object]) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    return None
