"""
Agent orchestration layer for A.R.T.E.M.I.S.

Provides LangGraph-based agent that routes between direct answers
and RAG-backed retrieval using the existing Retriever.
"""

from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.graph import AgentGraph

__all__ = [
    "AgentState",
    "AgentConfig",
    "AgentGraph",
    "run_agent",
    "run_agent_v2",
]


def __getattr__(name: str):
    """Lazy import run_agent/run_agent_v2 to avoid loading artemis.agent.run when package is imported (prevents RuntimeWarning when running python -m artemis.agent.run)."""
    if name == "run_agent":
        from artemis.agent.run import run_agent
        return run_agent
    if name == "run_agent_v2":
        from artemis.agent.run import run_agent_v2
        return run_agent_v2
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
