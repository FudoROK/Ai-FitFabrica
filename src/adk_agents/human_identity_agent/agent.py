"""FitFabrica human identity ADK agent assembly."""

from collections.abc import AsyncIterator

from google.adk.agents import llm_agent
from google.adk.sessions import vertex_ai_session_service
from vertexai.preview.reasoning_engines import AdkApp

from .contracts import HumanIdentityContract
from .prompt_config import HUMAN_IDENTITY_DESCRIPTION, HUMAN_IDENTITY_INSTRUCTION


VertexAiSessionService = vertex_ai_session_service.VertexAiSessionService


def session_service_builder() -> VertexAiSessionService:
    """Return the default ADK session service builder for runtime execution."""
    return VertexAiSessionService()


_root_llm_agent = llm_agent.LlmAgent(
    name="Human_Identity_Agent",
    model="gemini-2.5-flash",
    output_schema=HumanIdentityContract,
    description=HUMAN_IDENTITY_DESCRIPTION,
    sub_agents=[],
    instruction=HUMAN_IDENTITY_INSTRUCTION,
    tools=[],
)

root_agent = _root_llm_agent
_runtime_app = AdkApp(agent=root_agent, session_service_builder=session_service_builder)


async def stream_query(query: str, user_id: str = "test") -> AsyncIterator[object]:
    """Streaming query helper for local/runtime debugging."""
    async for chunk in _runtime_app.async_stream_query(message=query, user_id=user_id):
        yield chunk
