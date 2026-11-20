"""
Graph-mode retrieval: entity-link the query into the graph, traverse a few
hops, and format the resulting paths as {text, score, metadata} results --
the exact same shape semantic/keyword/hybrid produce, so this slots into
search_documents as another search_mode with no changes needed anywhere
else (reranking, API responses, eval harness all already handle this shape).
"""

from typing import Any, Dict, List

from artemis.graph.store import GraphStore


def graph_search(
    query: str,
    graph_store: GraphStore,
    tenant_id: str,
    k: int = 5,
    max_hops: int = 2,
) -> List[Dict[str, Any]]:
    """
    Multi-hop graph retrieval. Returns [] (not an error) when no entity in
    the query matches the graph -- that's a normal "graph has no relevant
    context for this question" outcome, same as semantic search returning
    no results above threshold.
    """
    entity_names = graph_store.find_matching_entities(tenant_id, query, limit=10)
    if not entity_names:
        return []

    paths = graph_store.traverse(tenant_id, entity_names, max_hops=max_hops, limit=max(k * 3, 15))
    paths.sort(key=lambda p: p["hops"])

    results: List[Dict[str, Any]] = []
    seen_texts = set()
    for path in paths:
        if not path["text"] or path["text"] in seen_texts:
            continue
        seen_texts.add(path["text"])
        results.append(
            {
                "text": path["text"],
                "score": 1.0 / (1 + path["hops"]),  # fewer hops = more directly relevant
                "metadata": {
                    "entities": path["entities"],
                    "source_docs": path["source_docs"],
                    "retrieval_mode": "graph",
                },
            }
        )
        if len(results) >= k:
            break
    return results


__all__ = ["graph_search"]
