"""
Tests for graph_search() (artemis/graph/search.py) scoring/dedup/formatting
logic, against a fake GraphStore -- no real Neo4j connection needed.
"""

from artemis.graph.search import graph_search


class _FakeGraphStore:
    def __init__(self, matched_entities, paths):
        self.matched_entities = matched_entities
        self.paths = paths
        self.find_calls = []
        self.traverse_calls = []

    def find_matching_entities(self, tenant_id, query, limit=10):
        self.find_calls.append((tenant_id, query, limit))
        return self.matched_entities

    def traverse(self, tenant_id, entity_names, max_hops=2, limit=25):
        self.traverse_calls.append((tenant_id, entity_names, max_hops, limit))
        return self.paths


def test_returns_empty_list_when_no_entity_matches():
    store = _FakeGraphStore(matched_entities=[], paths=[{"text": "should not appear", "entities": [], "source_docs": [], "hops": 1}])
    results = graph_search("unrelated question", store, "tenant_a")
    assert results == []
    assert store.traverse_calls == []  # shouldn't even bother traversing


def test_formats_paths_into_text_score_metadata_shape():
    store = _FakeGraphStore(
        matched_entities=["Director Sarah"],
        paths=[
            {"text": "Team Alpha reports_to Director Sarah", "entities": ["Team Alpha", "Director Sarah"], "source_docs": ["doc1"], "hops": 1},
        ],
    )
    results = graph_search("who does Sarah manage", store, "tenant_a", k=5)
    assert results == [
        {
            "text": "Team Alpha reports_to Director Sarah",
            "score": 0.5,
            "metadata": {"entities": ["Team Alpha", "Director Sarah"], "source_docs": ["doc1"], "retrieval_mode": "graph"},
        }
    ]


def test_sorts_shorter_paths_first_and_scores_them_higher():
    store = _FakeGraphStore(
        matched_entities=["X"],
        paths=[
            {"text": "far chain", "entities": [], "source_docs": [], "hops": 3},
            {"text": "direct link", "entities": [], "source_docs": [], "hops": 1},
        ],
    )
    results = graph_search("q", store, "tenant_a", k=5)
    assert [r["text"] for r in results] == ["direct link", "far chain"]
    assert results[0]["score"] > results[1]["score"]


def test_deduplicates_identical_path_text():
    store = _FakeGraphStore(
        matched_entities=["X"],
        paths=[
            {"text": "A rel B", "entities": [], "source_docs": [], "hops": 1},
            {"text": "A rel B", "entities": [], "source_docs": [], "hops": 1},
        ],
    )
    results = graph_search("q", store, "tenant_a", k=5)
    assert len(results) == 1


def test_respects_k_cap():
    paths = [{"text": f"path {i}", "entities": [], "source_docs": [], "hops": 1} for i in range(10)]
    store = _FakeGraphStore(matched_entities=["X"], paths=paths)
    results = graph_search("q", store, "tenant_a", k=3)
    assert len(results) == 3


def test_passes_tenant_id_through_to_the_store():
    store = _FakeGraphStore(matched_entities=["X"], paths=[])
    graph_search("q", store, "tenant_b", k=5, max_hops=4)
    assert store.find_calls[0][0] == "tenant_b"
    assert store.traverse_calls[0][0] == "tenant_b"
    assert store.traverse_calls[0][2] == 4  # max_hops threaded through
