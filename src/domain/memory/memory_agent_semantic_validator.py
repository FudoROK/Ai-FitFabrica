from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract

logger = logging.getLogger(__name__)


class MemorySemanticValidationOutcome(StrEnum):
    SEMANTIC_OK = "semantic_ok"
    SEMANTIC_REJECT_SOFT = "semantic_reject_soft"


@dataclass(frozen=True)
class MemorySemanticValidationResult:
    outcome: MemorySemanticValidationOutcome
    violation_codes: tuple[str, ...] = ()


class MemoryAgentSemanticValidator:
    """Semantic gate for memory-agent outputs before backend apply."""

    def validate(self, *, output: DailyMemoryContract) -> MemorySemanticValidationResult:
        violations: list[str] = []

        summary_text = (output.daily_summary.summary_text or "").strip()
        if not summary_text:
            violations.append("daily_summary_empty")

        if output.active_window_update and output.active_window_update.memory_relevance_flags:
            if any(flag.lower() in {"messages", "raw_messages", "history", "transcript"} for flag in output.active_window_update.memory_relevance_flags):
                violations.append("active_window_raw_message_marker")

        if violations:
            logger.warning(
                "memory_semantic_contract_violation",
                extra={
                    "violation_codes": list(violations),
                    "reason_code": violations[0],
                },
            )
            return MemorySemanticValidationResult(
                outcome=MemorySemanticValidationOutcome.SEMANTIC_REJECT_SOFT,
                violation_codes=tuple(violations),
            )

        logger.info("memory_semantic_validation_passed")
        return MemorySemanticValidationResult(outcome=MemorySemanticValidationOutcome.SEMANTIC_OK)
