"""Primary ADK agent assembly."""

from typing import Any

from google.adk.agents import llm_agent
from google.adk.sessions import vertex_ai_session_service
from vertexai.preview.reasoning_engines import AdkApp

from .contracts import AgentOutput
from .prompt_config import (
    QUALIFIER_INSTRUCTION, QUALIFIER_DESCRIPTION,
    ROUTER_INSTRUCTION, ROUTER_DESCRIPTION
)


VertexAiSessionService = vertex_ai_session_service.VertexAiSessionService


def session_service_builder() -> VertexAiSessionService:
    return VertexAiSessionService()

# Olaris Qualifier Sub-Agent
olaris_qualifier = llm_agent.LlmAgent(
    name="olaris_qualifier",
    model="gemini-2.5-flash",
    description=QUALIFIER_DESCRIPTION,
    sub_agents=[],
    instruction=QUALIFIER_INSTRUCTION,
    output_schema=AgentOutput,
    tools=[],
)

# Olaris Router Agent (main agent)
_root_llm_agent = llm_agent.LlmAgent(
    name="Olaris_Router",
    model="gemini-2.5-flash",
    description=ROUTER_DESCRIPTION,
    sub_agents=[olaris_qualifier],
    instruction=ROUTER_INSTRUCTION,
    output_schema=AgentOutput,
    tools=[],
)

root_agent = _root_llm_agent
_runtime_app = AdkApp(agent=root_agent, session_service_builder=session_service_builder)


async def stream_query(query: str, user_id: str = "test") -> Any:
    """Streaming query helper for local/runtime debugging."""
    async for chunk in _runtime_app.async_stream_query(message=query, user_id=user_id):
        yield chunk
