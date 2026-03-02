"""
Collection management sub-agent builder: filtered registry + CollectionManagementPrompt.
"""

from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.context import SystemContext
from artemis.agent.agents.base import SubAgentGraph, _filter_registry
from artemis.agent.prompts.collection_agent import CollectionManagementPrompt

COLLECTION_AGENT_TOOLS = [
    "list_collections",
    "get_collection_info",
    "create_collection",
    "clear_collection",
    "delete_collection",
]


def build_collection_agent(
    config: AgentConfig,
    registry: ToolRegistry,
    system_context: SystemContext,
    max_tool_steps: int = 4,
) -> SubAgentGraph:
    """
    max_tool_steps is 4 because the typical flow is:
    get_collection_info (check state) -> clear/delete (destructive op) -> direct (confirm)
    Keeping it tight prevents accidental loops on destructive operations.
    """
    filtered = _filter_registry(registry, COLLECTION_AGENT_TOOLS)
    return SubAgentGraph(
        config=config,
        registry=filtered,
        prompt=CollectionManagementPrompt(),
        system_context=system_context,
        max_tool_steps=max_tool_steps,
        agent_name="collection_management",
    )
