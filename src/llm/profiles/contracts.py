from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Mapping, Protocol, TypeVar, runtime_checkable

TypedOutputT = TypeVar("TypedOutputT")


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[ValidationError, ...] = field(default_factory=tuple)

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(ok=True, errors=())

    @classmethod
    def failure(cls, *errors: ValidationError) -> "ValidationResult":
        return cls(ok=False, errors=tuple(errors))


@dataclass(frozen=True)
class SemanticValidationContext:
    payload: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class FinalProfileInterface(Protocol, Generic[TypedOutputT]):
    """Canonical profile pipeline contract for all runtime profiles."""

    def parse(self, raw_payload: Any) -> TypedOutputT:
        ...

    def validate(self, typed_output: TypedOutputT) -> ValidationResult:
        ...

    def semantic_validate(
        self,
        typed_output: TypedOutputT,
        context: SemanticValidationContext,
    ) -> ValidationResult:
        ...


@runtime_checkable
class OrchestrationSuccessMapper(Protocol, Generic[TypedOutputT]):
    """Optional orchestration-level mapping hook (not part of profile runtime)."""

    def on_success(self, typed_output: TypedOutputT, context: Mapping[str, Any]) -> Mapping[str, Any]:
        ...
