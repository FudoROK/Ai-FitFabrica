from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictContractModel(BaseModel):
    """Base contract model with strict extra-field rejection for runtime boundaries."""

    model_config = ConfigDict(extra="forbid")
