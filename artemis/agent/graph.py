"""
LangGraph agent graph definition.

Planner chooses intent (tool vs direct). Tool node runs one tool and loops back
to planner. Direct answer node produces final_answer. No dedicated RAG path;
RAG is invoked via the tool registry when the planner selects search_documents.
"""

from typing import Literal

from langgraph.graph import StateGraph, END

from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.nodes.planner import planner_node
from artemis.agent.nodes.tool_node import tool_node
from artemis.agent.nodes.direct_answer import direct_answer_node
from artemis.utils import get_logger

logger = get_logger(__name__)


class AgentGraph:
    """
    LangGraph agent: planner -> direct_answer | tool_node -> planner (loop).

    Flow:
    1. START -> planner
    2. planner -> direct_answer (if intent=direct) -> END
    3. planner -> tool_node (if intent=tool) -> planner (loop) or direct_answer (if step limit)
    """

    def __init__(
        self,
        config: AgentConfig,
        registry: ToolRegistry,
        max_tool_steps: int = 10,
        current_collection: str | None = None,
    ):
        """
        Initialize agent graph.

        Args:
            config: Agent configuration
            registry: Tool registry (planner and tool_node use it)
            max_tool_steps: Max tool calls per run; after this, route to direct_answer
            current_collection: Name of the collection used for ingest/search this session (shown in planner so the agent can tell the user)
        """
        self.config = config
        self.registry = registry
        self.max_tool_steps = max_tool_steps
        self.current_collection = current_collection
        self.graph = self._build_graph()
        logger.info("Agent graph initialized with tool registry")

    def _build_graph(self) -> StateGraph:
        """Build and compile the LangGraph."""
        workflow = StateGraph(AgentState)

        workflow.add_node(
            "planner",
            lambda state: planner_node(
                state,
                self.config,
                self.registry,
                max_tool_steps=self.max_tool_steps,
                current_collection=self.current_collection,
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

        # tool_node -> planner (loop), or if at step limit -> direct_answer
        workflow.add_conditional_edges(
            "tool_node",
            self._route_after_tool,
            {"planner": "planner", "direct_answer": "direct_answer"},
        )

        return workflow.compile()

    def _route_after_planner(self, state: AgentState) -> Literal["direct", "tool"]:
        """Route from planner to direct_answer or tool_node."""
        intent = state.get("intent", "direct")
        logger.debug(f"Planner intent: {intent}")
        return intent

    def _route_after_tool(self, state: AgentState) -> Literal["planner", "direct_answer"]:
        """After tool_node: loop to planner or go to direct_answer if at step limit."""
        step_count = state.get("step_count", 0)
        if step_count >= self.max_tool_steps:
            logger.debug(f"Step limit {self.max_tool_steps} reached; routing to direct_answer")
            return "direct_answer"
        return "planner"

    def invoke(self, query: str) -> AgentState:
        """Run the agent with a query."""
        initial_state: AgentState = {
            "query": query,
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
        logger.info(f"Invoking agent with query: '{query[:50]}...'")
        result = self.graph.invoke(initial_state)
        logger.info("Agent execution completed")
        return result

    async def ainvoke(self, query: str) -> AgentState:
        """Async version of invoke."""
        initial_state: AgentState = {
            "query": query,
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
        logger.info(f"Async invoking agent with query: '{query[:50]}...'")
        result = await self.graph.ainvoke(initial_state)
        logger.info("Agent execution completed")
        return result
