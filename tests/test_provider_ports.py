from __future__ import annotations

from src.domain.provider_models import (
    EmbeddingRequest,
    ImageEditingRequest,
    ImageGenerationRequest,
    StructuredReasoningRequest,
)


def test_structured_reasoning_request_models_backend_owned_contract() -> None:
    request = StructuredReasoningRequest(
        task="dialog_reply_task",
        prompt="hello",
        response_schema={"type": "object"},
    )

    assert request.task == "dialog_reply_task"
    assert request.prompt == "hello"


def test_embedding_request_models_namespace_and_input() -> None:
    request = EmbeddingRequest(
        namespace="garments",
        input_text="black dress with belt",
    )

    assert request.namespace == "garments"
    assert request.input_text == "black dress with belt"


def test_image_generation_and_editing_requests_keep_backend_owned_references() -> None:
    generation_request = ImageGenerationRequest(
        task="product_card_generation",
        prompt="Generate a clean fashion image",
        output_mime_type="image/png",
    )
    editing_request = ImageEditingRequest(
        task="repair_try_on_result",
        prompt="Fix sleeve artifact",
        source_object_key="tenant-a/jobs/1/source.png",
        reference_object_keys=["tenant-a/jobs/1/garment.png"],
        output_mime_type="image/png",
    )

    assert generation_request.output_mime_type == "image/png"
    assert editing_request.source_object_key == "tenant-a/jobs/1/source.png"
    assert editing_request.reference_object_keys == ["tenant-a/jobs/1/garment.png"]
