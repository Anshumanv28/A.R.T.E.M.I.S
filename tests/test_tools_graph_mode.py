"""
Tests that build_rag_registry correctly wires graph_store into search_documents
(search_mode="graph") and ingest_file (extract_graph=True), across all three
retrieval configurations it supports (single retriever, retrievers dict,
multi-collection). Uses a fake GraphStore/LLM client -- no real Neo4j/LLM.
"""

from unittest.mock import patch

import pytest

from artemis.agent.tools import build_rag_registry
from artemis.rag.core.retriever import RetrievalMode


class _FakeRetriever:
    def retrieve(self, query, k=5):
        return [{"text": "vector result", "score": 0.9, "metadata": {}}]


class _FakeGraphStore:
    def __init__(self):
        self.upsert_calls = []

    def find_matching_entities(self, tenant_id, query, limit=10):
        return ["Director Sarah"] if "sarah" in query.lower() else []

    def traverse(self, tenant_id, entity_names, max_hops=2, limit=25):
        return [{"text": "Team Alpha reports_to Director Sarah", "entities": entity_names, "source_docs": ["d"], "hops": 1}]

    def upsert_graph(self, tenant_id, entities, relationships, source_doc):
        self.upsert_calls.append((tenant_id, entities, relationships, source_doc))


class _FakeLLMClient:
    def generate(self, system_prompt, user_prompt, **kwargs):
        import json
        return json.dumps({"entities": [{"name": "X", "type": "Other"}], "relationships": []})


def test_search_mode_graph_not_offered_without_a_graph_store():
    registry = build_rag_registry(retriever=_FakeRetriever(), graph_store=None)
    schema = registry.get("search_documents").parameters_schema
    assert "graph" not in schema["properties"]["search_mode"]["enum"]


def test_search_mode_graph_dispatches_to_graph_search_single_retriever():
    graph_store = _FakeGraphStore()
    registry = build_rag_registry(retriever=_FakeRetriever(), graph_store=graph_store, graph_tenant_id="tenant_a")
    schema = registry.get("search_documents").parameters_schema
    assert "graph" in schema["properties"]["search_mode"]["enum"]

    results = registry.get("search_documents").callable(query="what does Sarah manage", search_mode="graph")
    assert results == [
        {
            "text": "Team Alpha reports_to Director Sarah",
            "score": 0.5,
            "metadata": {"entities": ["Director Sarah"], "source_docs": ["d"], "retrieval_mode": "graph"},
        }
    ]


def test_search_mode_graph_dispatches_with_retrievers_dict():
    graph_store = _FakeGraphStore()
    registry = build_rag_registry(
        retriever=None,
        retrievers={"semantic": _FakeRetriever()},
        graph_store=graph_store,
        graph_tenant_id="tenant_a",
    )
    results = registry.get("search_documents").callable(query="sarah's team", search_mode="graph")
    assert results[0]["metadata"]["retrieval_mode"] == "graph"


def test_search_mode_graph_dispatches_with_multi_collection():
    graph_store = _FakeGraphStore()
    registry = build_rag_registry(
        retriever=None,
        indexers={"artemis_user_docs": object()},
        retrievers_by_collection={"artemis_user_docs": {"semantic": _FakeRetriever()}},
        default_collection="artemis_user_docs",
        graph_store=graph_store,
        graph_tenant_id="tenant_a",
    )
    results = registry.get("search_documents").callable(query="sarah's team", search_mode="graph")
    assert results[0]["metadata"]["retrieval_mode"] == "graph"


def test_search_mode_graph_returns_error_entry_when_not_configured_but_requested():
    """Defensive: if a caller explicitly passes search_mode="graph" with no graph_store, fail loudly, not silently fall through to semantic."""
    registry = build_rag_registry(retriever=_FakeRetriever(), graph_store=None)
    results = registry.get("search_documents").callable(query="x", search_mode="graph")
    assert results == [{"error": "Graph search mode is not available (no graph store configured)."}]


def test_graph_search_falls_through_to_vector_result_when_mode_is_not_graph():
    registry = build_rag_registry(retriever=_FakeRetriever(), graph_store=_FakeGraphStore())
    results = registry.get("search_documents").callable(query="x")
    assert results == [{"text": "vector result", "score": 0.9, "metadata": {}}]


def test_ingest_file_extract_graph_param_is_offered_only_with_graph_store(tmp_path):
    indexer_without_graph = type("FakeIndexer", (), {"collection_name": "c"})()
    registry_no_graph = build_rag_registry(retriever=_FakeRetriever(), indexer=indexer_without_graph, graph_store=None)
    schema = registry_no_graph.get("ingest_file").parameters_schema
    assert "extract_graph" not in schema["properties"]

    registry_with_graph = build_rag_registry(
        retriever=_FakeRetriever(), indexer=indexer_without_graph, graph_store=_FakeGraphStore()
    )
    schema = registry_with_graph.get("ingest_file").parameters_schema
    assert "extract_graph" in schema["properties"]


def test_ingest_file_extract_graph_calls_extraction_and_upsert(tmp_path):
    doc_path = tmp_path / "doc.txt"
    doc_path.write_text("Team Alpha manages Project Apollo.", encoding="utf-8")

    graph_store = _FakeGraphStore()
    fake_indexer = type("FakeIndexer", (), {"collection_name": "c"})()

    with patch("artemis.rag.tools.create_rag_ingest_tool") as mock_create_ingest_tool:
        mock_create_ingest_tool.return_value = lambda *a, **kw: {"ok": True, "path": str(doc_path), "file_type": "text"}
        registry = build_rag_registry(
            retriever=_FakeRetriever(),
            indexer=fake_indexer,
            graph_store=graph_store,
            llm_client_for_agentic=_FakeLLMClient(),
        )
        registry.get("ingest_file").callable(path=str(doc_path), file_type="text", extract_graph=True)

    assert len(graph_store.upsert_calls) == 1
    tenant_id, entities, relationships, source_doc = graph_store.upsert_calls[0]
    assert entities == [{"name": "X", "type": "Other"}]


def test_ingest_file_extract_graph_false_does_not_touch_graph_store(tmp_path):
    doc_path = tmp_path / "doc.txt"
    doc_path.write_text("Team Alpha manages Project Apollo.", encoding="utf-8")
    graph_store = _FakeGraphStore()
    fake_indexer = type("FakeIndexer", (), {"collection_name": "c"})()

    with patch("artemis.rag.tools.create_rag_ingest_tool") as mock_create_ingest_tool:
        mock_create_ingest_tool.return_value = lambda *a, **kw: {"ok": True, "path": str(doc_path), "file_type": "text"}
        registry = build_rag_registry(
            retriever=_FakeRetriever(),
            indexer=fake_indexer,
            graph_store=graph_store,
            llm_client_for_agentic=_FakeLLMClient(),
        )
        registry.get("ingest_file").callable(path=str(doc_path), file_type="text")

    assert graph_store.upsert_calls == []
