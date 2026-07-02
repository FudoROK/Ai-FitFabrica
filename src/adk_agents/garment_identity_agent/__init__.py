"""Contract exports for the FitFabrica garment identity agent."""

from .contracts import (
    GarmentIdentityContract,
    GarmentIdentityRequest,
    GarmentVisualDetail,
    GarmentWearControlCandidate,
    UnknownGarmentTaxonomyCandidate,
)

__all__ = [
    "GarmentIdentityRequest",
    "GarmentIdentityContract",
    "GarmentVisualDetail",
    "GarmentWearControlCandidate",
    "UnknownGarmentTaxonomyCandidate",
]
