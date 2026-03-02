"""
Sub-agent graph: reusable ReAct sub-agent with BasePrompt and filtered registry.
"""

from typing import List, Literal, Optional

from langgraph.graph import StateGraph, END

from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.context import SystemContext
from artemis.agent.prompts.base import BasePrompt
from artemis.agent.nodes.planner import planner_node
from artemis.agent.nodes.tool_node import tool_node
from artemis.agent.nodes.direct_answer import direct_answer_node
from artemis.utils import get_logger

logger = get_logger(__name__)


def _filter_registry(registry: ToolRegistry, tool_names: List[str]) -> ToolRegistry:
    """Return a new ToolRegistry with only the named tools. Skip missing names silently (log debug)."""
    new_registry = ToolRegistry()
    for name in tool_names:
        try:
            descriptor = registry.get(name)
            new_registry.register(
                name,
                descriptor.callable,
                descriptor.description,
                descriptor.parameters_schema,
            )
        except KeyError:
            logger.debug("Tool %s not in registry, skipping", name)
            continue
    return new_registry


class SubAgentGraph:
    """
    Reusable focused ReAct sub-agent.
    Same structure as AgentGraph but:
    - accepts a BasePrompt instance and a pre-filtered ToolRegistry
    - passes rendered system prompt to planner_node via system_prompt_override
    - max_tool_steps defaults to 5 (tighter than the top-level AgentGraph default of 10)
    """

    def __init__(
        self,
        config: AgentConfig,
        registry: ToolRegistry,
        prompt: BasePrompt,
        system_context: SystemContext,
        max_tool_steps: int = 5,
        agent_name: str = "sub_agent",
    ):
        self.config = config
        self.registry = registry
        self.prompt = prompt
        self.system_context = system_context
        self.max_tool_steps = max_tool_steps
        self.agent_name = agent_name
        self._rendered_system_prompt = self.prompt.render_system(self._build_prompt_context())
        self.graph = self._build_graph()
        logger.info("SubAgentGraph [%s] initialized", agent_name)

    def _build_prompt_context(self) -> dict:
        return {
            "collections": self.system_context.collections,
            "collection_info": self.system_context.collection_info,
            "search_modes": self.system_context.search_modes,
            "chunk_strategies": self.system_context.chunk_strategies,
            "csv_schemas": self.system_context.csv_schemas,
            "tools": self.registry.list_tools(),
            "max_tool_steps": self.max_tool_steps,
            "default_collection": (
                self.system_context.collections[0]
                if self.system_context.collections
                else "artemis_documents"
            ),
        }

    def _build_graph(self):
        """Build and compile the LangGraph. Same as AgentGraph except planner uses system_prompt_override."""
        workflow = StateGraph(AgentState)

        workflow.add_node(
            "planner",
            lambda state: planner_node(
                state,
                self.config,
                self.registry,
                max_tool_steps=self.max_tool_steps,
                system_prompt_override=self._rendered_system_prompt,
                current_collection=None,
            ),
        )
        workflow.add_node(
            "tool_node",
            lambda state: tool_node(state, self.registry),
        )
        workflow.add_node(
            "direct_answer",
            lambda state: direct_answer_node(state, self.config),
        )

        workflow.set_entry_point("planner")

        workflow.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {"direct": "direct_answer", "tool": "tool_node"},
        )

        workflow.add_edge("direct_answer", END)

        workflow.add_conditional_edges(
            "tool_node",
            self._route_after_tool,
            {"planner": "planner", "direct_answer": "direct_answer"},
        )

        return workflow.compile()

    def _route_after_planner(self, state: AgentState) -> Literal["direct", "tool"]:
        """Route from planner to direct_answer or tool_node."""
        intent = state.get("intent", "direct")
        logger.debug("Planner intent: %s", intent)
        return intent

    def _route_after_tool(self, state: AgentState) -> Literal["planner", "direct_answer"]:
        """After tool_node: loop to planner or go to direct_answer if at step limit."""
        step_count = state.get("step_count", 0)
        if step_count >= self.max_tool_steps:
            logger.debug("Step limit %s reached; routing to direct_answer", self.max_tool_steps)
            return "direct_answer"
        return "planner"

    def invoke(self, query: str, message_history: Optional[list] = None) -> AgentState:
        """Run the sub-agent with a query and optional conversation history."""
        initial_state: AgentState = {
            "query": query,
            "message_history": message_history,
            "intent": "direct",
            "confidence": 0.0,
            "tool_name": None,
            "tool_args": None,
            "retrieved_docs": [],
            "tool_calls": [],
            "step_count": 0,
            "tool_calls_summary": None,
            "final_answer": None,
            "error": None,
        }
        logger.info("Invoking sub-agent [%s] with query: '%s...'", self.agent_name, query[:50])
        result = self.graph.invoke(initial_state)
        logger.info("Sub-agent execution completed")
        return result

    async def ainvoke(self, query: str, message_history: Optional[list] = None) -> AgentState:
        """Async version of invoke."""
        initial_state: AgentState = {
            "query": query,
            "message_history": message_history,
            "intent": "direct",
            "confidence": 0.0,
            "tool_name": None,
            "tool_args": None,
            "retrieved_docs": [],
            "tool_calls": [],
            "step_count": 0,
            "tool_calls_summary": None,
            "final_answer": None,
            "error": None,
        }
        logger.info("Async invoking sub-agent [%s] with query: '%s...'", self.agent_name, query[:50])
        result = await self.graph.ainvoke(initial_state)
        logger.info("Sub-agent execution completed")
        return result
