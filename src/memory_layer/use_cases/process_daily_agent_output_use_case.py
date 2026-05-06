from __future__ import annotations

from dataclasses import dataclass
import logging

from pydantic import ValidationError

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from src.llm.profiles import ProfileRegistry, SemanticValidationContext
from src.services.runtime.feature_flags import FeatureFlags, resolve_feature_flags
from src.domain.memory.memory_agent_output_validator import MemoryAgentOutputValidator
from src.domain.memory.memory_agent_semantic_validator import (
    MemorySemanticValidationOutcome,
    MemorySemanticValidationResult,
    MemoryAgentSemanticValidator,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyAgentProcessingResult:
    accepted: bool
    output: DailyMemoryContract | None
    semantic_result: MemorySemanticValidationResult
    error_code: str | None = None
    retryable: bool = False
    error_message: str | None = None


class ProcessDailyAgentOutputUseCase:
    def __init__(
        self,
        *,
        validator: MemoryAgentOutputValidator | None = None,
        semantic_validator: MemoryAgentSemanticValidator | None = None,
        profile_registry: ProfileRegistry | None = None,
        feature_flags: FeatureFlags | None = None,
    ) -> None:
        self.validator = validator or MemoryAgentOutputValidator()
        self.semantic_validator = semantic_validator or MemoryAgentSemanticValidator()
        self.profile_registry = profile_registry or ProfileRegistry()
        self.feature_flags = feature_flags or resolve_feature_flags()

    def execute(
        self,
        *,
        payload: DailyMemoryContract | None,
        profile_enabled: bool | None = None,
        correlation_id: str | None = None,
    ) -> DailyAgentProcessingResult:
        runtime_enabled_by_flags = self.feature_flags.memory_runtime_enabled()
        effective_profile_enabled = runtime_enabled_by_flags if profile_enabled is None else bool(profile_enabled)

        if payload is None:
            logger.warning(
                "memory_profile_extraction",
                extra={"status": "extraction_not_found", "correlation_id": correlation_id},
            )
            return DailyAgentProcessingResult(
                accepted=False,
                output=None,
                semantic_result=MemorySemanticValidationResult(
                    outcome=MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                    violation_codes=("memory_output_missing",),
                ),
                error_code="extraction_not_found",
                retryable=False,
                error_message="memory_output_missing",
            )

        if effective_profile_enabled:
            profile = self.profile_registry.get_profile(flow="memory")
            logger.info(
                "memory_profile_registry_selected",
                extra={"profile": type(profile).__name__, "correlation_id": correlation_id},
            )
            try:
                typed = profile.parse(payload)
            except TypeError:
                logger.warning(
                    "memory_profile_contract_validation",
                    extra={"status": "contract_invalid", "correlation_id": correlation_id},
                )
                return DailyAgentProcessingResult(
                    accepted=False,
                    output=None,
                    semantic_result=MemorySemanticValidationResult(
                        outcome=MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                        violation_codes=("memory_profile_contract_invalid",),
                    ),
                    error_code="parser_contract_invalid",
                    retryable=False,
                    error_message="memory_profile_parse_type_error",
                )
            logger.info(
                "memory_profile_extraction",
                extra={"status": "success", "correlation_id": correlation_id},
            )
            profile_validation = profile.validate(typed)
            if not profile_validation.ok:
                logger.warning(
                    "memory_profile_contract_validation",
                    extra={"status": "contract_invalid", "correlation_id": correlation_id},
                )
                return DailyAgentProcessingResult(
                    accepted=False,
                    output=None,
                    semantic_result=MemorySemanticValidationResult(
                        outcome=MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                        violation_codes=("memory_profile_contract_invalid",),
                    ),
                    error_code="parser_contract_invalid",
                    retryable=False,
                    error_message="memory_profile_validation_failed",
                )
            logger.info(
                "memory_profile_contract_validation",
                extra={"status": "pass", "correlation_id": correlation_id},
            )
            profile_semantic = profile.semantic_validate(
                typed,
                SemanticValidationContext(payload={}),
            )
            if not profile_semantic.ok:
                logger.warning(
                    "memory_profile_semantic_validation",
                    extra={"status": "semantic_invalid", "correlation_id": correlation_id},
                )
                return DailyAgentProcessingResult(
                    accepted=False,
                    output=None,
                    semantic_result=MemorySemanticValidationResult(
                        outcome=MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                        violation_codes=("memory_profile_semantic_invalid",),
                    ),
                    error_code="domain_semantic_invalid",
                    retryable=False,
                    error_message="memory_profile_semantic_validation_failed",
                )
            logger.info(
                "memory_profile_semantic_validation",
                extra={"status": "pass", "correlation_id": correlation_id},
            )
            normalized_payload = typed.memory_payload
        else:
            normalized_payload = payload

        try:
            output = self.validator.validate(payload=normalized_payload)
        except ValidationError as exc:
            logger.warning(
                "memory_profile_contract_validation",
                extra={"status": "contract_invalid", "correlation_id": correlation_id},
            )
            return DailyAgentProcessingResult(
                accepted=False,
                output=None,
                semantic_result=MemorySemanticValidationResult(
                    outcome=MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                    violation_codes=("memory_output_schema_invalid",),
                ),
                error_code="parser_contract_invalid",
                retryable=False,
                error_message=str(exc),
            )

        semantic_result = self.semantic_validator.validate(output=output)
        if semantic_result.outcome == MemorySemanticValidationOutcome.SEMANTIC_OK:
            logger.info(
                "memory_profile_semantic_validation",
                extra={"status": "pass", "correlation_id": correlation_id},
            )
        else:
            logger.warning(
                "memory_profile_semantic_validation",
                extra={"status": "semantic_invalid", "correlation_id": correlation_id},
            )

        return DailyAgentProcessingResult(
            accepted=semantic_result.outcome == MemorySemanticValidationOutcome.SEMANTIC_OK,
            output=output,
            semantic_result=semantic_result,
            error_code=None if semantic_result.outcome == MemorySemanticValidationOutcome.SEMANTIC_OK else "domain_semantic_invalid",
            retryable=False,
            error_message=None,
        )
