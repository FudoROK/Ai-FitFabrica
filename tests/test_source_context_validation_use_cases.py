from __future__ import annotations

import pytest

from src.domain.context_validation import (
    ActorContext,
    ConfirmedFact,
    ContextStateQuery,
    ContextValidationErrorCode,
    SourceContextCandidate,
    SourceContextCandidateCommand,
    SourceContextCandidateStatus,
    SourceContextPayload,
    SourceContextValidationCommand,
    SourceReference,
    ValidationDecision,
)
from src.use_cases.context_validation import (
    QueryContextStateUseCase,
    RegisterSourceContextCandidateUseCase,
    ValidateSourceContextCandidateUseCase,
)


class _ContextRepository:
    """In-memory repository for source-context validation use-case tests."""

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
        """Return a confirmed fact by source candidate id."""
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


class _FailingContextRepository(_ContextRepository):
    """Repository that raises persistence errors for selected operations."""

    def __init__(self, *, fail_on: str) -> None:
        """Initialize the repository with the operation that should fail."""
        super().__init__()
        self.fail_on = fail_on

    async def get_candidate_by_correlation_id(self, *, correlation_id: str) -> SourceContextCandidate | None:
        """Raise or delegate candidate lookup by correlation id."""
        if self.fail_on == "get_candidate_by_correlation_id":
            raise RuntimeError("storage unavailable")
        return await super().get_candidate_by_correlation_id(correlation_id=correlation_id)

    async def get_candidate(self, *, candidate_id: str) -> SourceContextCandidate | None:
        """Raise or delegate candidate lookup."""
        if self.fail_on == "get_candidate":
            raise RuntimeError("storage unavailable")
        return await super().get_candidate(candidate_id=candidate_id)

    async def save_candidate(self, *, candidate: SourceContextCandidate) -> None:
        """Raise or delegate candidate persistence."""
        if self.fail_on == "save_candidate":
            raise RuntimeError("storage unavailable")
        await super().save_candidate(candidate=candidate)

    async def save_confirmed_fact(self, *, confirmed_fact: ConfirmedFact) -> None:
        """Raise or delegate confirmed fact persistence."""
        if self.fail_on == "save_confirmed_fact":
            raise RuntimeError("storage unavailable")
        await super().save_confirmed_fact(confirmed_fact=confirmed_fact)

    async def save_candidate_with_confirmed_fact(
        self,
        *,
        candidate: SourceContextCandidate,
        confirmed_fact: ConfirmedFact,
    ) -> None:
        """Raise or delegate atomic promotion persistence."""
        if self.fail_on == "save_candidate_with_confirmed_fact":
            raise RuntimeError("storage unavailable")
        await super().save_candidate_with_confirmed_fact(candidate=candidate, confirmed_fact=confirmed_fact)

    async def list_candidates(self, *, tenant_id: str) -> list[SourceContextCandidate]:
        """Raise or delegate candidate listing."""
        if self.fail_on == "list_candidates":
            raise RuntimeError("storage unavailable")
        return await super().list_candidates(tenant_id=tenant_id)


def _command(*, correlation_id: str = "corr-1") -> SourceContextCandidateCommand:
    """Build a valid candidate command."""
    return SourceContextCandidateCommand(
        payload=SourceContextPayload(fact_key="business_type", value="retail", summary="Business type is retail."),
        source_reference=SourceReference(source_type="telegram", source_id="msg-1"),
        actor_context=ActorContext(tenant_id="tenant-1", actor_id="user-1", session_id="session-1"),
        correlation_id=correlation_id,
    )


@pytest.mark.asyncio
async def test_candidate_creation_is_pending_and_idempotent_without_confirmed_fact() -> None:
    """Candidate creation writes pending state and never creates confirmed facts."""
    repo = _ContextRepository()
    use_case = RegisterSourceContextCandidateUseCase(repository=repo)

    first = await use_case.execute(command=_command())
    second = await use_case.execute(command=_command())

    assert first.ok is True
    assert first.candidate is not None
    assert first.candidate.status == SourceContextCandidateStatus.PENDING_CONFIRMATION
    assert first.candidate.warnings == ["source_excerpt_missing"]
    assert second.candidate == first.candidate
    assert repo.facts == {}


@pytest.mark.asyncio
async def test_candidate_creation_rejects_correlation_reuse_across_actor_contexts() -> None:
    """Candidate idempotency cannot return another actor context's candidate."""
    repo = _ContextRepository()
    first = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert first.ok is True

    cross_tenant_command = SourceContextCandidateCommand(
        payload=SourceContextPayload(fact_key="business_type", value="retail", summary="Business type is retail."),
        source_reference=SourceReference(source_type="telegram", source_id="msg-1"),
        actor_context=ActorContext(tenant_id="tenant-2", actor_id="user-1", session_id="session-1"),
        correlation_id="corr-1",
    )
    result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=cross_tenant_command)

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ContextValidationErrorCode.MISSING_AUTHORITY


@pytest.mark.asyncio
async def test_confirm_transition_promotes_candidate_to_confirmed_fact() -> None:
    """Confirming a pending candidate creates a separate confirmed fact."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None

    result = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-1",
            reason="explicit user confirmation",
        )
    )

    assert result.ok is True
    assert result.candidate is not None
    assert result.confirmed_fact is not None
    assert result.candidate.status == SourceContextCandidateStatus.CONFIRMED
    assert result.confirmed_fact.value == "retail"


@pytest.mark.asyncio
async def test_validation_rejects_cross_tenant_or_wrong_actor_context() -> None:
    """Validation commands cannot change candidates owned by another actor context."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None

    result = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=ActorContext(tenant_id="tenant-2", actor_id="user-1", session_id="session-1"),
            correlation_id="validate-cross-tenant",
        )
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ContextValidationErrorCode.MISSING_AUTHORITY
    assert repo.facts == {}


@pytest.mark.asyncio
async def test_refine_requires_refined_value_and_promotes_refined_fact() -> None:
    """Refine decisions require replacement content before promotion."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None

    result = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.REFINE,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-2",
            refined_value="online retail",
        )
    )

    assert result.ok is True
    assert result.candidate is not None
    assert result.confirmed_fact is not None
    assert result.candidate.status == SourceContextCandidateStatus.REFINED
    assert result.confirmed_fact.value == "online retail"


@pytest.mark.asyncio
async def test_query_keeps_candidates_separate_from_confirmed_facts() -> None:
    """Query results expose candidates and confirmed facts as separate collections."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None
    await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-3",
        )
    )

    result = await QueryContextStateUseCase(repository=repo).execute(
        query=ContextStateQuery(actor_context=create_result.candidate.actor_context)
    )

    assert len(result.candidates) == 1
    assert len(result.confirmed_facts) == 1
    assert result.candidates[0].candidate_id == result.confirmed_facts[0].candidate_id


@pytest.mark.asyncio
async def test_keep_open_candidate_can_later_be_resolved() -> None:
    """A keep-open decision defers resolution without blocking later confirmation."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None
    keep_open = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.KEEP_OPEN,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-open",
        )
    )
    assert keep_open.ok is True
    assert keep_open.candidate is not None
    assert keep_open.candidate.status == SourceContextCandidateStatus.OPEN

    confirmed = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-after-open",
        )
    )

    assert confirmed.ok is True
    assert confirmed.confirmed_fact is not None


@pytest.mark.asyncio
async def test_query_filters_candidates_and_facts_to_actor_context() -> None:
    """Context queries do not expose another actor/session's candidates or facts."""
    repo = _ContextRepository()
    first = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command(correlation_id="corr-1"))
    second = await RegisterSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextCandidateCommand(
            payload=SourceContextPayload(fact_key="need", value="automation", summary="Needs automation."),
            source_reference=SourceReference(source_type="telegram", source_id="msg-2"),
            actor_context=ActorContext(tenant_id="tenant-1", actor_id="user-2", session_id="session-2"),
            correlation_id="corr-2",
        )
    )
    assert first.candidate is not None
    assert second.candidate is not None
    await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=first.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=first.candidate.actor_context,
            correlation_id="validate-first",
        )
    )
    await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=second.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=second.candidate.actor_context,
            correlation_id="validate-second",
        )
    )

    result = await QueryContextStateUseCase(repository=repo).execute(
        query=ContextStateQuery(actor_context=first.candidate.actor_context)
    )

    assert [candidate.candidate_id for candidate in result.candidates] == [first.candidate.candidate_id]
    assert [fact.candidate_id for fact in result.confirmed_facts] == [first.candidate.candidate_id]


@pytest.mark.asyncio
async def test_candidate_creation_returns_structured_persistence_failure() -> None:
    """Candidate creation maps repository failures to structured backend errors."""
    result = await RegisterSourceContextCandidateUseCase(
        repository=_FailingContextRepository(fail_on="get_candidate_by_correlation_id")
    ).execute(command=_command())

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ContextValidationErrorCode.PERSISTENCE_FAILURE


@pytest.mark.asyncio
async def test_validation_promotion_returns_structured_persistence_failure() -> None:
    """Validation promotion maps persistence failures to structured backend errors."""
    repo = _FailingContextRepository(fail_on="save_candidate_with_confirmed_fact")
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None

    result = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-storage-failure",
        )
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ContextValidationErrorCode.PERSISTENCE_FAILURE
    assert repo.candidates[create_result.candidate.candidate_id].status == SourceContextCandidateStatus.PENDING_CONFIRMATION


@pytest.mark.asyncio
async def test_repeated_validation_rejects_conflicting_promotion_command() -> None:
    """Only the same repeated promotion is idempotent; conflicting decisions fail."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None
    first = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.CONFIRM,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-first",
        )
    )
    assert first.ok is True

    conflict = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.REFINE,
            actor_context=create_result.candidate.actor_context,
            correlation_id="validate-conflict",
            refined_value="online retail",
        )
    )

    assert conflict.ok is False
    assert conflict.error is not None
    assert conflict.error.code == ContextValidationErrorCode.INVALID_TRANSITION


@pytest.mark.asyncio
async def test_repeated_reject_decision_is_idempotent() -> None:
    """Retrying the same reject decision returns the current rejected candidate."""
    repo = _ContextRepository()
    create_result = await RegisterSourceContextCandidateUseCase(repository=repo).execute(command=_command())
    assert create_result.candidate is not None
    first = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.REJECT,
            actor_context=create_result.candidate.actor_context,
            correlation_id="reject-first",
        )
    )
    assert first.ok is True
    assert first.candidate is not None
    assert first.candidate.status == SourceContextCandidateStatus.REJECTED

    second = await ValidateSourceContextCandidateUseCase(repository=repo).execute(
        command=SourceContextValidationCommand(
            candidate_id=create_result.candidate.candidate_id,
            decision=ValidationDecision.REJECT,
            actor_context=create_result.candidate.actor_context,
            correlation_id="reject-retry",
        )
    )

    assert second.ok is True
    assert second.candidate is not None
    assert second.candidate.status == SourceContextCandidateStatus.REJECTED


@pytest.mark.asyncio
async def test_query_returns_structured_persistence_failure() -> None:
    """Context-state queries map repository failures to structured backend errors."""
    result = await QueryContextStateUseCase(repository=_FailingContextRepository(fail_on="list_candidates")).execute(
        query=ContextStateQuery(actor_context=ActorContext(tenant_id="tenant-1", actor_id="user-1"))
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == ContextValidationErrorCode.PERSISTENCE_FAILURE
