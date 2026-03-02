"""
RAG Search sub-agent builder: filtered registry + RAGSearchPrompt.
"""

from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.context import SystemContext
from artemis.agent.agents.base import SubAgentGraph, _filter_registry
from artemis.agent.prompts.rag_agent import RAGSearchPrompt

RAG_AGENT_TOOLS = [
    "search_documents",
    "list_collections",
    "get_collection_info",
    "get_rag_options",
]


def build_rag_agent(
    config: AgentConfig,
    registry: ToolRegistry,
    system_context: SystemContext,
    max_tool_steps: int = 5,
) -> SubAgentGraph:
    filtered = _filter_registry(registry, RAG_AGENT_TOOLS)
    return SubAgentGraph(
        config=config,
        registry=filtered,
        prompt=RAGSearchPrompt(),
        system_context=system_context,
        max_tool_steps=max_tool_steps,
        agent_name="rag_search",
    )
