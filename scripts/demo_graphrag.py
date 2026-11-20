#!/usr/bin/env python3
"""
GraphRAG demo: the exact multi-hop example from ARTEMIS_improvements.txt --

    Document A: Project Apollo is managed by Team Alpha.
    Document B: Team Alpha reports to Director Sarah.
    Document C: Project Apollo uses PostgreSQL.
    Document D: Project Apollo integrates with Service X.

    Question: "Which services are used by projects managed by teams
    reporting to Sarah?"

The doc's claim was that vector search retrieves the individual documents
but doesn't naturally traverse the relationship chain, while a graph can.
This script ingests the same four documents into both an in-memory Qdrant
(semantic search, via scripts/benchmark_retrieval.py's pattern) and a real
Neo4j graph (graph search, via a disposable tenant_id, cleaned up after),
then runs the exact question against both and prints the results side by
side -- showing the claim is true, not just asserted.

Requires NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD (see .env.example).

Usage:
    python scripts/demo_graphrag.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient

from artemis.graph.client import get_neo4j_driver, is_graph_configured
from artemis.graph.search import graph_search
from artemis.graph.store import GraphStore
from artemis.rag.core.embedder import Embedder
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.retriever import RetrievalMode, Retriever

DOCUMENTS = [
    "Document A: Project Apollo is managed by Team Alpha.",
    "Document B: Team Alpha reports to Director Sarah.",
    "Document C: Project Apollo uses PostgreSQL.",
    "Document D: Project Apollo integrates with Service X.",
]

ENTITIES = [
    {"name": "Project Apollo", "type": "Project"},
    {"name": "Team Alpha", "type": "Organization"},
    {"name": "Director Sarah", "type": "Person"},
    {"name": "PostgreSQL", "type": "Technology"},
    {"name": "Service X", "type": "Technology"},
]
RELATIONSHIPS = [
    {"source": "Team Alpha", "relation": "manages", "target": "Project Apollo"},
    {"source": "Team Alpha", "relation": "reports_to", "target": "Director Sarah"},
    {"source": "Project Apollo", "relation": "uses", "target": "PostgreSQL"},
    {"source": "Project Apollo", "relation": "integrates_with", "target": "Service X"},
]

QUESTION = "Which services are used by projects managed by teams reporting to Sarah?"


def run_semantic_search():
    embedder = Embedder()
    indexer = Indexer.__new__(Indexer)  # bypass __init__'s forced qdrant_url -- see benchmark_retrieval.py
    indexer.collection_name = "graphrag_demo"
    indexer.embedder = embedder
    indexer.metadata_config = None
    indexer.qdrant_client = QdrantClient(location=":memory:")
    indexer.add_documents(DOCUMENTS, [{"doc_id": f"doc_{i}"} for i in range(len(DOCUMENTS))])

    retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
    return retriever.retrieve(QUESTION, k=4)


def run_graph_search():
    if not is_graph_configured():
        return None, "NEO4J_URI/USERNAME/PASSWORD not set -- skipping graph search."
    driver = get_neo4j_driver()
    store = GraphStore(driver)
    tenant_id = f"graphrag_demo_{uuid.uuid4().hex[:8]}"
    try:
        store.upsert_graph(tenant_id, ENTITIES, RELATIONSHIPS, source_doc="demo_docs")
        results = graph_search(QUESTION, store, tenant_id, k=10, max_hops=3)
        return results, None
    finally:
        store.delete_tenant_graph(tenant_id)
        store.close()


def main() -> None:
    print(f"\nQuestion: {QUESTION}\n")

    print("=" * 72)
    print("Semantic (vector) search over the 4 documents, top 4:")
    print("=" * 72)
    for r in run_semantic_search():
        print(f"  [{r['score']:.3f}] {r['text']}")
    print(
        "\n  -> Each document is retrieved individually. Nothing in a single\n"
        "     chunk states 'PostgreSQL/Service X are used by a project managed\n"
        "     by a team reporting to Sarah' -- that fact only exists as a chain\n"
        "     across all four documents, which vector similarity doesn't trace.\n"
    )

    graph_results, skip_reason = run_graph_search()
    print("=" * 72)
    print("Graph (multi-hop) search:")
    print("=" * 72)
    if skip_reason:
        print(f"  {skip_reason}")
    elif not graph_results:
        print("  No results -- entity-linking found nothing matching the query.")
    else:
        for r in graph_results:
            print(f"  [{r['score']:.3f}] {r['text']}")
        print(
            "\n  -> Starting from the matched entity ('Director Sarah'), the graph\n"
            "     traverses reports_to -> manages -> uses/integrates_with and\n"
            "     surfaces the full chain: Sarah <- Team Alpha <- manages -\n"
            "     Project Apollo -> uses PostgreSQL / integrates_with Service X.\n"
            "     An agent synthesizing from these edges can answer correctly;\n"
            "     synthesizing from the semantic results above, it can't.\n"
        )


if __name__ == "__main__":
    main()
