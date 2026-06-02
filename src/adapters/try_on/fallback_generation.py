"""Fallback wrapper for guarded Try-On generation rollouts."""

from __future__ import annotations

import logging

from src.domain.try_on import TryOnGenerationMode, TryOnInputMetadata, TryOnResult, TryOnStoredInput
from src.use_cases.try_on.ports import TryOnGenerationPort

logger = logging.getLogger(__name__)


class FallbackTryOnGenerationAdapter(TryOnGenerationPort):
    """Run a primary generator first and fall back only on explicit rollout failures."""

    generation_mode = TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON

    def __init__(
        self,
        *,
        primary: TryOnGenerationPort,
        fallback: TryOnGenerationPort,
        fallback_backend_name: str,
    ) -> None:
        """Store the guarded primary and the explicitly approved fallback adapter."""
        self._primary = primary
        self._fallback = fallback
        self._fallback_backend_name = fallback_backend_name

    async def generate(
        self,
        *,
        job_id: str,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
    ) -> TryOnResult:
        """Attempt the primary generator and use fallback only when the primary raises."""
        try:
            return await self._primary.generate(
                job_id=job_id,
                input_metadata=input_metadata,
                stored_inputs=stored_inputs,
            )
        except Exception:
            logger.exception(
                "Real Vertex Try-On generation failed; using configured fallback backend.",
                extra={"try_on_fallback_backend": self._fallback_backend_name, "job_id": job_id},
            )
            return await self._fallback.generate(
                job_id=job_id,
                input_metadata=input_metadata,
                stored_inputs=stored_inputs,
            )
