"""
GraphRAG: entity/relationship extraction and multi-hop graph retrieval,
backed by Neo4j, complementing (not replacing) Qdrant vector search.
Entirely optional -- see artemis.graph.client.is_graph_configured().
"""

from artemis.graph.client import get_neo4j_driver, is_graph_configured
from artemis.graph.extraction import extract_entities_and_relationships
from artemis.graph.search import graph_search
from artemis.graph.store import GraphStore

__all__ = [
    "get_neo4j_driver",
    "is_graph_configured",
    "extract_entities_and_relationships",
    "graph_search",
    "GraphStore",
]
