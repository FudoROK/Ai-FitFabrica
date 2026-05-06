"""Dialog send-step wiring over unified step-idempotency policy."""
from __future__ import annotations

from src.use_cases.dialog import SendReplyUseCase
from ..runtime.step_idempotency import StepIdempotencyPolicy


def build_send_reply_use_case(*, messaging) -> SendReplyUseCase:
    """Create SendReplyUseCase with canonical step-idempotency policy."""
    return SendReplyUseCase(
        messaging=messaging,
        step_idempotency=StepIdempotencyPolicy(),
    )
