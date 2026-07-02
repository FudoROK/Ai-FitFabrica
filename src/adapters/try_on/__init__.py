"""Try-On adapters for sandbox and provider-runtime generation paths."""

from .deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from .deterministic_repair_adapter import DeterministicTryOnRepairAdapter
from .deterministic_stylist import DeterministicTryOnStylist
from .fallback_generation import FallbackTryOnGenerationAdapter
from .fake_generation import FakeTryOnGenerationAdapter
from .model_backed_quality_verifier import ModelBackedTryOnQualityVerifier
from .model_backed_stylist import ModelBackedTryOnStylist
from .provider_repair_adapter import ProviderRuntimeTryOnRepairAdapter
from .provider_generation import TryOnProviderGenerationAdapter

__all__ = [
    "DeterministicTryOnQualityVerifier",
    "DeterministicTryOnRepairAdapter",
    "DeterministicTryOnStylist",
    "FallbackTryOnGenerationAdapter",
    "FakeTryOnGenerationAdapter",
    "ModelBackedTryOnQualityVerifier",
    "ModelBackedTryOnStylist",
    "ProviderRuntimeTryOnRepairAdapter",
    "TryOnProviderGenerationAdapter",
    "TryOnQualityVerifierAgentAdapter",
    "VertexVirtualTryOnGenerationAdapter",
]


def __getattr__(name: str):
    """Load heavy provider adapters only when callers explicitly request them."""

    if name == "VertexVirtualTryOnGenerationAdapter":
        from .vertex_virtual_try_on_generation import VertexVirtualTryOnGenerationAdapter

        return VertexVirtualTryOnGenerationAdapter
    if name == "TryOnQualityVerifierAgentAdapter":
        from .quality_verifier_agent_adapter import TryOnQualityVerifierAgentAdapter

        return TryOnQualityVerifierAgentAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
