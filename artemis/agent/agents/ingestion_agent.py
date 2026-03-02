"""
Ingestion sub-agent builder: filtered registry + IngestionPrompt.
"""

from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.context import SystemContext
from artemis.agent.agents.base import SubAgentGraph, _filter_registry
from artemis.agent.prompts.ingestion_agent import IngestionPrompt

INGESTION_AGENT_TOOLS = [
    "list_directory",
    "suggest_ingest_options",
    "ingest_file",
    "ingest_directory",
    "get_rag_options",
    "list_collections",
    "create_collection",
]


def build_ingestion_agent(
    config: AgentConfig,
    registry: ToolRegistry,
    system_context: SystemContext,
    max_tool_steps: int = 6,
) -> SubAgentGraph:
    filtered = _filter_registry(registry, INGESTION_AGENT_TOOLS)
    return SubAgentGraph(
        config=config,
        registry=filtered,
        prompt=IngestionPrompt(),
        system_context=system_context,
        max_tool_steps=max_tool_steps,
        agent_name="ingestion",
    )
