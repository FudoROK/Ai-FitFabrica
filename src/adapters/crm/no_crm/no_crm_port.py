from __future__ import annotations

import logging

from src.domain.contracts.crm_port import CRMOperationRequest, CRMOperationResult, CRMOperationStatus

logger = logging.getLogger(__name__)


class DisabledCRMPort:
    """CRMPort implementation for environments without a configured CRM."""

    async def execute(self, *, request: CRMOperationRequest) -> CRMOperationResult:
        """Return a structured disabled result without provider side effects."""
        logger.info(
            "crm_operation_disabled",
            extra={
                "operation": request.operation,
                "entity_ref": request.entity_ref,
                "tenant_id": request.tenant_id,
            },
        )
        return CRMOperationResult(
            status=CRMOperationStatus.DISABLED,
            provider=None,
            provider_reference=None,
            message="CRM provider is disabled or not configured.",
            retryable=False,
        )
