from __future__ import annotations

from typing import Any

from src.domain.crm import derive_lead_state_flags
from src.domain.extraction import extract_patch, non_empty_patch


class IngestLeadPatchUseCase:
    def __init__(self, *, leads_repo) -> None:
        self.leads_repo = leads_repo

    async def execute(
        self,
        *,
        lead_id: str | None,
        payload: Any,
        external_user_id: str | int | None = None,
    ) -> bool:
        if not lead_id:
            return False

        lead_patch = extract_patch(payload)
        sanitized_patch = non_empty_patch({}, lead_patch)
        if not sanitized_patch:
            return False

        if external_user_id is not None:
            sanitized_patch["channel_user_id"] = str(external_user_id)

        sanitized_patch.update(derive_lead_state_flags(sanitized_patch))

        await self.leads_repo.apply_lead_patch(lead_id, sanitized_patch)
        return True