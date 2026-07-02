"""Provider-neutral Product Card generation through the canonical agent runtime."""

from __future__ import annotations

from src.adk_agents.product_card_agent.contracts import ProductCardContentContract
from src.adk_agents.product_card_agent.deploy_config import ProductCardAgentDeployConfig
from src.adk_agents.product_card_agent.prompt_config import PRODUCT_CARD_AGENT_INSTRUCTION
from src.domain.agent_runtime import AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.product_card import ProductCardDraft, ProductCardGarmentAnalysis, ProductCardRequest
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.product_card.generation_errors import ProductCardGenerationFailure
from src.use_cases.product_card.ports import ProductCardGenerationPort

class ProductCardAgentGenerationAdapter(ProductCardGenerationPort):
    """Generate Product Card drafts through a replaceable agent provider."""

    def __init__(
        self,
        *,
        invocation_service: AgentInvocationService,
        timeout_seconds: float,
        preferred_model: str | None,
    ) -> None:
        """Store portable runtime dependencies."""
        self._invocation_service = invocation_service
        self._timeout_seconds = timeout_seconds
        self._preferred_model = preferred_model
        self._config = ProductCardAgentDeployConfig()

    async def generate(
        self,
        *,
        request: ProductCardRequest,
        garment_analysis: ProductCardGarmentAnalysis,
    ) -> ProductCardDraft:
        """Invoke the Product Card agent and map its validated output."""
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=garment_analysis.job_id,
                prompt=PRODUCT_CARD_AGENT_INSTRUCTION,
                input_payload={
                    "title_hint": request.title_hint,
                    "category": request.category,
                    "target_channel": request.target_channel,
                    "brand_tone": request.brand_tone,
                    "garment_analysis": garment_analysis.model_dump(mode="json"),
                },
                artifact_references=[],
                response_schema=ProductCardContentContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=ProductCardContentContract,
        )
        if (
            envelope.status != AgentRuntimeStatus.SUCCEEDED
            or envelope.validation_status != AgentValidationStatus.PASSED
            or envelope.output is None
        ):
            raise ProductCardGenerationFailure(
                safe_code=envelope.error.code if envelope.error is not None else "product_card_invalid_output"
            )
        output = ProductCardContentContract.model_validate(envelope.output)
        return ProductCardDraft(
            title=output.title,
            description=output.short_description,
            bullet_points=list(output.key_attributes),
            attributes={
                "category": request.category,
                "target_channel": request.target_channel,
                "confidence": str(output.confidence),
                "merchandising_notes": " | ".join(output.merchandising_notes),
                "limitations": " | ".join(output.limitations),
            },
        )
