"""Typed settings projections used by runtime code."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    mode: str
    model: str
    vertex_project: Optional[str]
    vertex_location: Optional[str]
    vertex_agent_resource: Optional[str]


@dataclass(frozen=True)
class CRMSettings:
    crm_access_token: Optional[str]
    crm_base_url: str
    sync_enabled: bool
