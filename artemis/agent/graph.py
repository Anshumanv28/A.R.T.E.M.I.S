"""
LangGraph agent graph definition.

Wires together planner, RAG node, and direct answer node with conditional routing.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.rag.core.retriever import Retriever
from artemis.agent.nodes.planner import planner_node
from artemis.agent.nodes.rag_node import rag_node
from artemis.agent.nodes.direct_answer import direct_answer_node
from artemis.utils import get_logger

logger = get_logger(__name__)


class AgentGraph:
    """
    LangGraph agent that routes between RAG and direct answer paths.
    
    Flow:
    1. Start -> planner (classify intent)
    2. planner -> rag_node (if intent="rag")
    3. planner -> direct_answer_node (if intent="direct")
    4. Both paths -> END
    """
    
    def __init__(self, config: AgentConfig, retriever: Retriever):
        """
        Initialize agent graph.
        
        Args:
            config: Agent configuration
            retriever: Retriever instance for RAG node
        """
        self.config = config
        self.retriever = retriever
        
        # Build graph
        self.graph = self._build_graph()
        logger.info("Agent graph initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build and compile the LangGraph."""
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", lambda state: planner_node(state, self.config))
        workflow.add_node(
            "rag_node",
            lambda state: rag_node(state, self.config, self.retriever)
        )
        workflow.add_node(
            "direct_answer",
            lambda state: direct_answer_node(state, self.config)
        )
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Add conditional edges from planner
        workflow.add_conditional_edges(
            "planner",
            self._route_after_planner,
            {
                "rag": "rag_node",
                "direct": "direct_answer"
            }
        )
        
        # Both paths end
        workflow.add_edge("rag_node", END)
        workflow.add_edge("direct_answer", END)
        
        # Compile graph
        return workflow.compile()
    
    def _route_after_planner(self, state: AgentState) -> Literal["rag", "direct"]:
        """
        Route after planner node based on intent.
        
        Args:
            state: Current agent state
            
        Returns:
            "rag" or "direct"
        """
        intent = state.get("intent", "rag")
        logger.debug(f"Routing to: {intent}")
        return intent
    
    def invoke(self, query: str) -> AgentState:
        """
        Run the agent with a query.
        
        Args:
            query: User query string
            
        Returns:
            Final agent state with answer
        """
        initial_state: AgentState = {
            "query": query,
            "intent": "rag",  # Default, will be set by planner
            "confidence": 0.0,
            "retrieved_docs": [],
            "tool_calls": [],
            "final_answer": None,
            "error": None
        }
        
        logger.info(f"Invoking agent with query: '{query[:50]}...'")
        result = self.graph.invoke(initial_state)
        logger.info("Agent execution completed")
        
        return result
    
    async def ainvoke(self, query: str) -> AgentState:
        """
        Async version of invoke.
        
        Args:
            query: User query string
            
        Returns:
            Final agent state with answer
        """
        initial_state: AgentState = {
            "query": query,
            "intent": "rag",
            "confidence": 0.0,
            "retrieved_docs": [],
            "tool_calls": [],
            "final_answer": None,
            "error": None
        }
        
        logger.info(f"Async invoking agent with query: '{query[:50]}...'")
        result = await self.graph.ainvoke(initial_state)
        logger.info("Agent execution completed")
        
        return result
