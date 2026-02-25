"""
State schema for LangGraph agent.

Defines the state structure that flows through the agent graph.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class AgentState(TypedDict):
    """
    State schema for the LangGraph agent.
    
    This state flows through all nodes in the graph and accumulates
    information as the agent processes a query.
    """
    # Input
    query: str
    
    # Intent classification
    intent: Literal["rag", "direct"]
    confidence: float  # 0.0 to 1.0
    
    # RAG results
    retrieved_docs: List[Dict[str, Any]]  # List of {text, score, metadata}
    
    # Tool execution (future)
    tool_calls: List[Dict[str, Any]]
    
    # Final output
    final_answer: Optional[str]
    
    # Error handling
    error: Optional[str]
