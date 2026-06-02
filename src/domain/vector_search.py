"""Typed domain models for vector retrieval."""

from __future__ import annotations

from enum import StrEnum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field

VectorPayloadValue: TypeAlias = str | int | float | bool


class VectorNamespace(StrEnum):
    """Approved logical namespaces for vector retrieval."""

    GARMENTS = "garments"
    PRODUCTS = "products"
    PERSONA_STYLE = "persona_style"
    RECOGNITION = "recognition"


class VectorPointRecord(BaseModel):
    """One vector point stored in the retrieval layer."""

    model_config = ConfigDict(extra="forbid")

    point_id: str = Field(min_length=1)
    namespace: VectorNamespace
    embedding: list[float] = Field(min_length=1)
    payload: dict[str, VectorPayloadValue] = Field(default_factory=dict)
    owner_id: str = Field(min_length=1)


class VectorSearchQuery(BaseModel):
    """Typed query used for vector similarity search."""

    model_config = ConfigDict(extra="forbid")

    namespace: VectorNamespace
    embedding: list[float] = Field(min_length=1)
    limit: int = Field(default=10, gt=0)
    search_filter: VectorSearchFilter | None = None


class VectorSearchFilter(BaseModel):
    """Typed payload filters applied alongside vector similarity search."""

    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    brand: str | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)


class VectorSearchHit(BaseModel):
    """Typed similarity-search hit returned from the retrieval layer."""

    model_config = ConfigDict(extra="forbid")

    point_id: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    namespace: VectorNamespace
    score: float
    payload: dict[str, VectorPayloadValue] = Field(default_factory=dict)
