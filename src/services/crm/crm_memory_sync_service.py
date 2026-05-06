"""Downstream CRM memory sync side-effects for memory summaries."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable, Optional

from .crm_service import (
    crm_enabled,
    crm_memory_sync_enabled,
    crm_provider,
    crm_sync_enabled,
    find_contact_ref_by_channel_user_id,
    update_contact_memory,
)
from ..runtime.step_idempotency import StepContext, StepIdempotencyPolicy
from src.services.runtime.step_keys import StepKeys

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CrmMemorySyncResult:
    ok: bool
    reason_code: str | None = None


class CrmMemorySyncService:
    """Handles CRM memory sync feature gating, idempotency and side effects."""

    def __init__(
        self,
        *,
        leads_repo,
        crm_sync_enabled_fn: Optional[Callable[[], bool]] = None,
        crm_memory_sync_enabled_fn: Optional[Callable[[], bool]] = None,
        crm_enabled_fn: Optional[Callable[[], bool]] = None,
        crm_provider_fn: Optional[Callable[[], str]] = None,
        find_contact_ref_by_channel_user_id_fn: Optional[Callable[[str], Optional[str]]] = None,
        step_idempotency: Optional[StepIdempotencyPolicy] = None,
        update_contact_memory_fn: Optional[Callable[..., object]] = None,
    ) -> None:
        self.leads_repo = leads_repo
        self.crm_sync_enabled_fn = crm_sync_enabled_fn or crm_sync_enabled
        self.crm_memory_sync_enabled_fn = crm_memory_sync_enabled_fn or crm_memory_sync_enabled
        self.crm_enabled_fn = crm_enabled_fn or crm_enabled
        self.crm_provider_fn = crm_provider_fn or crm_provider
        self.find_contact_ref_by_channel_user_id_fn = (
            find_contact_ref_by_channel_user_id_fn or find_contact_ref_by_channel_user_id
        )
        self.step_idempotency = step_idempotency or StepIdempotencyPolicy()
        self.update_contact_memory_fn = update_contact_memory_fn or update_contact_memory

    async def sync_memory(
        self,
        *,
        lead_id: str,
        lead_data: dict,
        daily_summary: Optional[str],
        daily_date: str,
        rolling_summary: Optional[str],
        rolling_version: int | None,
        rolling_hash: str | None,
        errors: list[str],
    ) -> CrmMemorySyncResult:
        if not self.crm_sync_enabled_fn() or not self.crm_memory_sync_enabled_fn() or not self.crm_enabled_fn():
            return CrmMemorySyncResult(ok=False, reason_code="crm_sync_disabled")
        logger.info("crm_memory_sync_started", extra={"lead_id": lead_id})
        contact_ref = lead_data.get("crm_contact_ref")
        if not contact_ref:
            channel_user_id = lead_data.get("channel_user_id")
            if channel_user_id:
                contact_ref = self.find_contact_ref_by_channel_user_id_fn(str(channel_user_id))
            if contact_ref:
                await self.leads_repo.upsert_crm_contact_binding(
                    lead_id=lead_id,
                    crm_contact_ref=str(contact_ref),
                    crm_provider=self.crm_provider_fn(),
                )
        if not contact_ref:
            message = f"CRM contact not found for lead {lead_id}"
            errors.append(message)
            logger.info("crm_memory_sync_failed", extra={"lead_id": lead_id, "reason": "contact_not_found"})
            return CrmMemorySyncResult(ok=False, reason_code="crm_contact_not_found")

        normalized_rolling_hash = str(rolling_hash or "").strip()
        if rolling_version is None or not isinstance(rolling_version, int) or rolling_version < 1:
            message = f"CRM rolling version missing or invalid for lead {lead_id}"
            errors.append(message)
            logger.info("crm_memory_sync_failed", extra={"lead_id": lead_id, "reason": "rolling_version_missing_or_invalid"})
            return CrmMemorySyncResult(ok=False, reason_code="rolling_version_missing_or_invalid")
        if not normalized_rolling_hash:
            message = f"CRM rolling hash missing or invalid for lead {lead_id}"
            errors.append(message)
            logger.info("crm_memory_sync_failed", extra={"lead_id": lead_id, "reason": "rolling_hash_missing_or_invalid"})
            return CrmMemorySyncResult(ok=False, reason_code="rolling_hash_missing_or_invalid")

        context = StepContext(
            lead_id=lead_id,
            daily_date=daily_date,
            rolling_version=rolling_version,
            rolling_hash=normalized_rolling_hash,
        )
        if self.step_idempotency.is_step_completed(step=StepKeys.CRM_SYNC_MEMORY, context=context):
            return CrmMemorySyncResult(ok=True, reason_code="crm_sync_already_completed")

        try:
            update_ok = bool(
                self.update_contact_memory_fn(
                contact_ref=str(contact_ref),
                daily_text=daily_summary,
                daily_date=daily_date,
                rolling_text=rolling_summary,
                rolling_version=rolling_version,
                rolling_hash=normalized_rolling_hash,
                )
            )
            if not update_ok:
                message = f"CRM memory sync failed for {lead_id}: provider update rejected"
                errors.append(message)
                logger.info(
                    "crm_memory_sync_failed",
                    extra={"lead_id": lead_id, "crm_contact_ref": contact_ref, "reason": "crm_sync_update_failed"},
                )
                return CrmMemorySyncResult(ok=False, reason_code="crm_sync_update_failed")
            self.step_idempotency.mark_step_completed(
                step=StepKeys.CRM_SYNC_MEMORY,
                context=context,
                metadata={
                    "crm_contact_ref": str(contact_ref),
                    "rolling_version": rolling_version,
                    "rolling_hash": normalized_rolling_hash,
                },
            )
            logger.info("crm_memory_sync_ok", extra={"lead_id": lead_id, "crm_contact_ref": contact_ref})
            return CrmMemorySyncResult(ok=True, reason_code=None)
        except Exception as exc:  # pragma: no cover - defensive logging
            message = f"CRM memory sync failed for {lead_id}: {exc}"
            errors.append(message)
            logger.exception("crm_memory_sync_failed", extra={"lead_id": lead_id, "crm_contact_ref": contact_ref})
            return CrmMemorySyncResult(ok=False, reason_code="crm_sync_update_failed")
