"""Provider-neutral ports for AI-facing backend integrations."""

from __future__ import annotations

from typing import Protocol

from src.domain.provider_models import (
    EmbeddingRequest,
    EmbeddingResult,
    ImageEditingRequest,
    ImageEditingResult,
    ImageGenerationRequest,
    ImageGenerationResult,
    StructuredReasoningRequest,
    StructuredReasoningResult,
)
from src.llm.core.request import LLMRequest
from src.llm.core.result import LLMResult


class StructuredReasoningPort(Protocol):
    """Port for providers that return structured reasoning payloads."""

    provider_name: str

    def generate(self, request: LLMRequest) -> LLMResult:
        """Run the provider through the existing LLM request contract."""

    def generate_structured(self, request: StructuredReasoningRequest) -> StructuredReasoningResult:
        """Optional high-level backend contract for structured reasoning."""


class AgentRuntimePort(Protocol):
    """Port for agent-runtime style providers."""

    provider_name: str

    def generate(self, request: LLMRequest) -> LLMResult:
        """Run the provider through the existing LLM request contract."""


class EmbeddingProviderPort(Protocol):
    """Port for embedding generation."""

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Create an embedding for backend-owned text input."""


class ImageGenerationPort(Protocol):
    """Port for image generation backends."""

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate an image artifact reference."""


class ImageEditingPort(Protocol):
    """Port for image editing backends."""

    def edit(self, request: ImageEditingRequest) -> ImageEditingResult:
        """Edit an existing image artifact and return a new reference."""
