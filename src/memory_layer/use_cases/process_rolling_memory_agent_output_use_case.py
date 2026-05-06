from __future__ import annotations

from dataclasses import dataclass
import logging

from src.runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from src.domain.memory.rolling_content_policy import validate as validate_rolling_content

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RollingMemorySemanticResult:
    ok: bool
    violation_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RollingMemoryAgentProcessingResult:
    accepted: bool
    output: RollingMemoryContract | None
    semantic_result: RollingMemorySemanticResult
    error_code: str | None = None
    retryable: bool = False
    error_message: str | None = None


class ProcessRollingMemoryAgentOutputUseCase:
    """Validate rolling-agent output independently from daily flow."""

    def execute(
        self,
        *,
        payload: RollingMemoryContract | None,
        profile_enabled: bool | None = None,
        correlation_id: str | None = None,
    ) -> RollingMemoryAgentProcessingResult:
        _ = profile_enabled
        if payload is None:
            return RollingMemoryAgentProcessingResult(
                accepted=False,
                output=None,
                semantic_result=RollingMemorySemanticResult(ok=False, violation_codes=("rolling_output_missing",)),
                error_code="extraction_not_found",
                retryable=False,
                error_message="rolling_output_missing",
            )

        try:
            output = payload if isinstance(payload, RollingMemoryContract) else RollingMemoryContract.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "rolling_profile_contract_validation",
                extra={"status": "contract_invalid", "correlation_id": correlation_id},
            )
            return RollingMemoryAgentProcessingResult(
                accepted=False,
                output=None,
                semantic_result=RollingMemorySemanticResult(ok=False, violation_codes=("rolling_output_schema_invalid",)),
                error_code="parser_contract_invalid",
                retryable=False,
                error_message=str(exc),
            )

        content_check = validate_rolling_content(output.rolling_update.rolling_summary_text)
        if not content_check.ok:
            return RollingMemoryAgentProcessingResult(
                accepted=False,
                output=None,
                semantic_result=RollingMemorySemanticResult(
                    ok=False,
                    violation_codes=(str(content_check.reason_code or "rolling_semantic_invalid"),),
                ),
                error_code="domain_semantic_invalid",
                retryable=False,
                error_message=content_check.reason_code,
            )

        return RollingMemoryAgentProcessingResult(
            accepted=True,
            output=output,
            semantic_result=RollingMemorySemanticResult(ok=True),
            error_code=None,
            retryable=False,
            error_message=None,
        )
