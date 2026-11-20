"""
Web Search sub-agent builder: filtered registry + WebSearchPrompt.
"""

from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.context import SystemContext
from artemis.agent.agents.base import SubAgentGraph, _filter_registry
from artemis.agent.prompts.web_search_agent import WebSearchPrompt

WEB_SEARCH_AGENT_TOOLS = ["web_search"]


def build_web_search_agent(
    config: AgentConfig,
    registry: ToolRegistry,
    system_context: SystemContext,
    max_tool_steps: int = 5,
) -> SubAgentGraph:
    filtered = _filter_registry(registry, WEB_SEARCH_AGENT_TOOLS)
    return SubAgentGraph(
        config=config,
        registry=filtered,
        prompt=WebSearchPrompt(),
        system_context=system_context,
        max_tool_steps=max_tool_steps,
        agent_name="web_search",
    )
