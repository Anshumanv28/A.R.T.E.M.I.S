"""
A tenant (or the default single-tenant deployment) can create_collection()
with an arbitrary new name and immediately search_documents/ingest into it,
without restarting the process -- previously only the two standard
collections baked in at registry-build time were searchable/ingestible.

Runs fully offline: an embedded (":memory:") Qdrant instance stands in for
the real server, and create_collection_tool/delete_collection_tool (which
go through their own separate module-level Qdrant client in
artemis/rag/tools.py, keyed off QDRANT_URL) are stubbed out since this test
is about the registry's own indexers/retrievers_by_collection wiring, not
Qdrant connectivity.
"""

import pytest
from qdrant_client import QdrantClient

from artemis.agent.tools import build_rag_registry
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.retriever import Retriever, RetrievalMode

NOT_AVAILABLE_ERROR = "Collection 'notes' is not available. Create it with create_collection then retry."


def _in_memory_qdrant_client(*args, **kwargs):
    return QdrantClient(location=":memory:")


@pytest.fixture(scope="module")
def shared_embedder():
    from artemis.rag.core.embedder import Embedder
    return Embedder()


@pytest.fixture
def multi_collection_registry(monkeypatch, shared_embedder):
    monkeypatch.setattr("artemis.rag.core.indexer.QdrantClient", _in_memory_qdrant_client)
    monkeypatch.setattr("artemis.rag.tools.create_collection_tool", lambda name, embedding_dim=None: True)
    monkeypatch.setattr("artemis.rag.tools.delete_collection_tool", lambda name, confirm=False: bool(confirm))

    embedder = shared_embedder
    idx_system = Indexer(collection_name="artemis_system_docs", embedder=embedder)
    idx_user = Indexer(collection_name="artemis_user_docs", embedder=embedder)
    indexers = {"artemis_system_docs": idx_system, "artemis_user_docs": idx_user}
    retrievers_by_collection = {
        "artemis_system_docs": {"semantic": Retriever(mode=RetrievalMode.SEMANTIC, indexer=idx_system)},
        "artemis_user_docs": {"semantic": Retriever(mode=RetrievalMode.SEMANTIC, indexer=idx_user)},
    }
    registry = build_rag_registry(
        retriever=None,
        indexer=None,
        indexers=indexers,
        retrievers_by_collection=retrievers_by_collection,
        default_collection="artemis_user_docs",
    )
    return registry, indexers, retrievers_by_collection


def test_new_collection_is_not_searchable_before_creation(multi_collection_registry):
    registry, _, _ = multi_collection_registry
    result = registry.get("search_documents").callable(query="hello", collection_name="notes")
    assert result == [{"error": NOT_AVAILABLE_ERROR}]


def test_create_collection_wires_it_for_immediate_search_and_ingest(multi_collection_registry):
    registry, indexers, retrievers_by_collection = multi_collection_registry

    created = registry.get("create_collection").callable(collection_name="notes")
    assert created["ok"] is True
    assert "notes" in indexers
    assert "notes" in retrievers_by_collection
    assert "semantic" in retrievers_by_collection["notes"]

    # Simulates what ingest_file would do: add real content to the newly wired collection.
    indexers["notes"].add_documents(["hello world"], [{"doc_id": "d1"}])

    result = registry.get("search_documents").callable(query="hello", collection_name="notes", k=3)
    assert result and result[0]["text"] == "hello world"


def test_get_rag_options_reflects_newly_created_collection(multi_collection_registry):
    registry, _, _ = multi_collection_registry
    before = registry.get("get_rag_options").callable()
    assert "notes" not in before["collections"]

    registry.get("create_collection").callable(collection_name="notes")

    after = registry.get("get_rag_options").callable()
    assert "notes" in after["collections"]


def test_delete_collection_unwires_it_from_search(multi_collection_registry):
    registry, indexers, retrievers_by_collection = multi_collection_registry

    registry.get("create_collection").callable(collection_name="notes")
    assert "notes" in indexers

    deleted = registry.get("delete_collection").callable(collection_name="notes", confirm=True)
    assert deleted is True
    assert "notes" not in indexers
    assert "notes" not in retrievers_by_collection

    result = registry.get("search_documents").callable(query="hello", collection_name="notes")
    assert result == [{"error": NOT_AVAILABLE_ERROR}]
