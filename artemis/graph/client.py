"""
Neo4j connection helper for GraphRAG, mirroring artemis/rag/core/collection_manager.py's
get_qdrant_client() pattern: read connection details from env vars, raise a clear
error if missing, and let every other caller stay agnostic of where they come from.
"""

import os
from typing import Optional

from artemis.utils import get_logger

logger = get_logger(__name__)

try:
    from neo4j import Driver, GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    Driver = None
    GraphDatabase = None
    NEO4J_AVAILABLE = False


def is_graph_configured() -> bool:
    """True iff the neo4j driver is installed and NEO4J_URI/USERNAME/PASSWORD are all set."""
    return bool(
        NEO4J_AVAILABLE
        and os.environ.get("NEO4J_URI")
        and os.environ.get("NEO4J_USERNAME")
        and os.environ.get("NEO4J_PASSWORD")
    )


def get_neo4j_driver(
    uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> "Driver":
    """
    Build a Neo4j driver from explicit args or NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD.

    Raises ImportError if the neo4j package isn't installed, ValueError if
    connection details are missing. Callers that want graceful degradation
    (GraphRAG is optional, like TAVILY_API_KEY) should check is_graph_configured()
    first instead of catching these.
    """
    if not NEO4J_AVAILABLE:
        raise ImportError("neo4j package is required for GraphRAG. Install it with: pip install neo4j")

    uri = uri or os.environ.get("NEO4J_URI")
    username = username or os.environ.get("NEO4J_USERNAME")
    password = password or os.environ.get("NEO4J_PASSWORD")
    if not (uri and username and password):
        raise ValueError(
            "Neo4j connection details are required. Set NEO4J_URI, NEO4J_USERNAME, "
            "and NEO4J_PASSWORD in the environment, or pass them explicitly."
        )
    logger.debug("Connecting to Neo4j at %s", uri)
    return GraphDatabase.driver(uri, auth=(username, password))


__all__ = ["get_neo4j_driver", "is_graph_configured", "NEO4J_AVAILABLE"]
