"""
Least-privilege scopes for the MCP server: reuse the existing per-sub-agent
tool allow-lists verbatim rather than defining a new access model.
"""

from typing import Dict, List, Optional

from artemis.agent.agents.rag_agent import RAG_AGENT_TOOLS
from artemis.agent.agents.ingestion_agent import INGESTION_AGENT_TOOLS
from artemis.agent.agents.collection_agent import COLLECTION_AGENT_TOOLS

# None means "no filtering" (every tool in the registry).
MCP_SCOPES: Dict[str, Optional[List[str]]] = {
    "rag_search": RAG_AGENT_TOOLS,
    "ingestion": INGESTION_AGENT_TOOLS,
    "collection_management": COLLECTION_AGENT_TOOLS,
    "full": None,
}

# rag_search is the only scope with zero mutating tools; everything else must be requested explicitly.
DEFAULT_SCOPE = "rag_search"

__all__ = ["MCP_SCOPES", "DEFAULT_SCOPE"]
