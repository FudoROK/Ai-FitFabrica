from __future__ import annotations

import pytest

from src.domain.context_validation import (
    ActorContext,
    ConfirmedFact,
    ContextValidationErrorCode,
    SourceContextCandidate,
    SourceContextCandidateStatus,
    ValidationDecision,
)
from src.use_cases.context_validation import ApplySourceContextAgentIntentUseCase
from src.use_cases.context_validation.agent_intent import SourceContextValidationIntent


class _ContextRepository:
    """In-memory repository for agent intent orchestration tests."""

    def __init__(self) -> None:
        """Initialize empty candidate and confirmed fact stores."""
        self.candidates: dict[str, SourceContextCandidate] = {}
        self.facts: dict[str, ConfirmedFact] = {}

    async def get_candidate_by_correlation_id(self, *, correlation_id: str) -> SourceContextCandidate | None:
        """Return a candidate by correlation id."""
        return next((item for item in self.candidates.values() if item.correlation_id == correlation_id), None)

    async def get_candidate(self, *, candidate_id: str) -> SourceContextCandidate | None:
        """Return a candidate by id."""
        return self.candidates.get(candidate_id)

    async def save_candidate(self, *, candidate: SourceContextCandidate) -> None:
        """Persist candidate state."""
        self.candidates[candidate.candidate_id] = candidate

    async def get_confirmed_fact_by_candidate_id(self, *, candidate_id: str) -> ConfirmedFact | None:
        """Return a confirmed fact by candidate id."""
        return next((item for item in self.facts.values() if item.candidate_id == candidate_id), None)

    async def save_confirmed_fact(self, *, confirmed_fact: ConfirmedFact) -> None:
        """Persist confirmed fact state."""
        self.facts[confirmed_fact.fact_id] = confirmed_fact

    async def save_candidate_with_confirmed_fact(
        self,
        *,
        candidate: SourceContextCandidate,
        confirmed_fact: ConfirmedFact,
    ) -> None:
        """Persist candidate promotion and confirmed fact atomically."""
        self.candidates[candidate.candidate_id] = candidate
        self.facts[confirmed_fact.fact_id] = confirmed_fact

    async def list_candidates(self, *, tenant_id: str) -> list[SourceContextCandidate]:
        """List tenant candidates."""
        return [item for item in self.candidates.values() if item.actor_context.tenant_id == tenant_id]

    async def list_confirmed_facts(self, *, tenant_id: str) -> list[ConfirmedFact]:
        """List tenant confirmed facts."""
        return [item for item in self.facts.values() if item.tenant_id == tenant_id]


def test_agent_intent_accepts_structured_candidate_and_recommendation() -> None:
    """Agent intent parsing accepts only structured source-context JSON."""
    intent = SourceContextValidationIntent.parse_agent_payload(
        {
            "candidate_proposals": [
                {
                    "payload": {
                        "fact_key": "need",
                        "value": "automation",
                        "summary": "The lead needs automation.",
                    },
                    "source_reference": {
                        "source_type": "telegram",
                        "source_id": "msg-1",
                        "source_excerpt": "Need automation",
                    },
                    "confidence": 0.8,
                }
            ],
            "validation_recommendations": [
                {
                    "candidate_id": "ctx-1",
                    "decision": ValidationDecision.KEEP_OPEN.value,
                    "reason": "needs user confirmation",
                }
            ],
        }
    )

    assert len(intent.candidate_proposals) == 1
    assert intent.validation_recommendations[0].decision == ValidationDecision.KEEP_OPEN


def test_agent_intent_rejects_malformed_or_unsupported_output() -> None:
    """Malformed agent output is rejected before backend state changes."""
    with pytest.raises(ValueError, match="invalid_source_context_validation_intent"):
        SourceContextValidationIntent.parse_agent_payload(
            {
                "candidate_proposals": [],
                "validation_recommendations": [{"candidate_id": "ctx-1", "decision": "persist_directly"}],
            }
        )


@pytest.mark.asyncio
async def test_agent_intent_use_case_maps_valid_proposals_to_backend_commands() -> None:
    """Backend orchestration applies valid agent proposals through candidate commands."""
    repo = _ContextRepository()
    result = await ApplySourceContextAgentIntentUseCase(repository=repo).execute(
        agent_payload={
            "candidate_proposals": [
                {
                    "payload": {
                        "fact_key": "need",
                        "value": "automation",
                        "summary": "The lead needs automation.",
                    },
                    "source_reference": {"source_type": "telegram", "source_id": "msg-1"},
                    "confidence": 0.9,
                }
            ],
            "validation_recommendations": [],
        },
        actor_context=ActorContext(tenant_id="tenant-1", actor_id="user-1", session_id="session-1"),
        correlation_id="agent-1",
    )

    assert result.ok is True
    assert len(repo.candidates) == 1
    candidate = next(iter(repo.candidates.values()))
    assert candidate.status == SourceContextCandidateStatus.PENDING_CONFIRMATION
    assert repo.facts == {}


@pytest.mark.asyncio
async def test_agent_intent_use_case_rejects_malformed_payload_before_writes() -> None:
    """Malformed agent output produces a structured error and no persistence writes."""
    repo = _ContextRepository()
    result = await ApplySourceContextAgentIntentUseCase(repository=repo).execute(
        agent_payload={"validation_recommendations": [{"candidate_id": "ctx-1", "decision": "persist_directly"}]},
        actor_context=ActorContext(tenant_id="tenant-1", actor_id="user-1"),
        correlation_id="agent-bad",
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ContextValidationErrorCode.INVALID_INPUT
    assert repo.candidates == {}
    assert repo.facts == {}
