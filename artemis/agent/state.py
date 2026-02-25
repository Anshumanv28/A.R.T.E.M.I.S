"""
State schema for LangGraph agent.

Defines the state structure that flows through the agent graph.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class AgentState(TypedDict, total=False):
    """
    State schema for the LangGraph agent.

    This state flows through all nodes in the graph and accumulates
    information as the agent processes a query.
    """
    # Input
    query: str

    # Intent classification: "tool" = run a tool, "direct" = answer without tools
    intent: Literal["tool", "direct"]
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Planner reasoning (optional)

    # Tool selection (set by planner when intent == "tool")
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]

    # RAG results (backward compatibility; tool node may set when last tool was search)
    retrieved_docs: List[Dict[str, Any]]  # List of {text, score, metadata}

    # Tool execution history: each entry is {tool_name, arguments, result, ok}
    tool_calls: List[Dict[str, Any]]
    step_count: int  # Number of tool steps taken; used to cap iterations

    # Pre-summarized tool results for direct_answer prompt (set by tool node or helper)
    tool_calls_summary: Optional[str]

    # Final output
    final_answer: Optional[str]

    # Error handling
    error: Optional[str]
