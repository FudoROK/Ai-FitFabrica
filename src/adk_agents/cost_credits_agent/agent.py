"""FitFabrica cost and credits ADK agent assembly."""

from typing import Any

from google.adk.agents import llm_agent
from google.adk.sessions import vertex_ai_session_service
from vertexai.preview.reasoning_engines import AdkApp

from .contracts import CostCreditsExplanationContract
from .prompt_config import COST_CREDITS_AGENT_DESCRIPTION, COST_CREDITS_AGENT_INSTRUCTION


VertexAiSessionService = vertex_ai_session_service.VertexAiSessionService


def session_service_builder() -> VertexAiSessionService:
    """Return the default ADK session service builder for runtime execution."""
    return VertexAiSessionService()


_root_llm_agent = llm_agent.LlmAgent(
    name="Cost_Credits_Agent",
    model="gemini-2.5-flash",
    output_schema=CostCreditsExplanationContract,
    description=COST_CREDITS_AGENT_DESCRIPTION,
    sub_agents=[],
    instruction=COST_CREDITS_AGENT_INSTRUCTION,
    tools=[],
)

root_agent = _root_llm_agent
_runtime_app = AdkApp(agent=root_agent, session_service_builder=session_service_builder)


async def stream_query(query: str, user_id: str = "test") -> Any:
    """Streaming query helper for local/runtime debugging."""
    async for chunk in _runtime_app.async_stream_query(message=query, user_id=user_id):
        yield chunk
