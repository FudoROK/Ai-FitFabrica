"""Rolling memory ADK agent assembly."""

from typing import Any

from google.adk.agents import llm_agent
from google.adk.sessions import vertex_ai_session_service
from vertexai.preview.reasoning_engines import AdkApp

from .contracts import RollingMemoryContract
from .prompt_config import ROLLING_MEMORY_INSTRUCTION, ROLLING_MEMORY_DESCRIPTION


VertexAiSessionService = vertex_ai_session_service.VertexAiSessionService


def session_service_builder() -> VertexAiSessionService:
    return VertexAiSessionService()

_root_llm_agent = llm_agent.LlmAgent(
    name="Rolling_Memory_Agent",
    model="gemini-2.5-flash",
    output_schema=RollingMemoryContract,
    description=ROLLING_MEMORY_DESCRIPTION,
    sub_agents=[],
    instruction=ROLLING_MEMORY_INSTRUCTION,
    tools=[],
)

root_agent = _root_llm_agent
_runtime_app = AdkApp(agent=root_agent, session_service_builder=session_service_builder)


async def stream_query(query: str, user_id: str = "test") -> Any:
    """Streaming query helper for local/runtime debugging."""
    async for chunk in _runtime_app.async_stream_query(message=query, user_id=user_id):
        yield chunk
