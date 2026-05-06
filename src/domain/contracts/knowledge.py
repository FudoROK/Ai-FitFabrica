from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class KnowledgeContract(ABC):
    @abstractmethod
    def search_knowledge(self, *, query: str, limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_document(self, *, document_id: str) -> Optional[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def semantic_lookup(self, *, query: str, limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError
