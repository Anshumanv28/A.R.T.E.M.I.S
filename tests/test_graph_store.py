"""
Integration tests for GraphStore against a real Neo4j instance (AuraDB free
tier or local). Skipped entirely if NEO4J_URI/USERNAME/PASSWORD aren't set --
same pattern as test_integration.py's Qdrant/LLM skipif.

Uses a disposable tenant_id ("artemis_test_<random>") and deletes everything
it created in a module-scoped fixture teardown, so repeated runs never
accumulate leftover data and never touch a real tenant's graph.
"""

import uuid

import pytest

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from project root, same convention as test_restaurant_converter.py
except ImportError:
    pass  # python-dotenv not installed, will use system env vars only

from artemis.graph.client import get_neo4j_driver, is_graph_configured
from artemis.graph.store import GraphStore

pytestmark = pytest.mark.skipif(
    not is_graph_configured(),
    reason="Graph store integration tests require NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD",
)

TEST_ENTITIES = [
    {"name": "Project Apollo", "type": "Project"},
    {"name": "Team Alpha", "type": "Organization"},
    {"name": "Director Sarah", "type": "Person"},
    {"name": "PostgreSQL", "type": "Technology"},
]
TEST_RELATIONSHIPS = [
    {"source": "Team Alpha", "relation": "manages", "target": "Project Apollo"},
    {"source": "Team Alpha", "relation": "reports_to", "target": "Director Sarah"},
    {"source": "Project Apollo", "relation": "uses", "target": "PostgreSQL"},
]


@pytest.fixture(scope="module")
def tenant_id():
    return f"artemis_test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def store(tenant_id):
    driver = get_neo4j_driver()
    graph_store = GraphStore(driver)
    graph_store.upsert_graph(tenant_id, TEST_ENTITIES, TEST_RELATIONSHIPS, source_doc="test_doc.md")
    yield graph_store
    graph_store.delete_tenant_graph(tenant_id)
    graph_store.close()


def test_find_matching_entities_matches_on_partial_name(store, tenant_id):
    """Query says "Sarah", entity is named "Director Sarah" -- word-level match, not whole-name substring."""
    matches = store.find_matching_entities(tenant_id, "What does Sarah's team manage?")
    assert "Director Sarah" in matches


def test_find_matching_entities_returns_empty_for_unrelated_query(store, tenant_id):
    assert store.find_matching_entities(tenant_id, "completely unrelated question about weather") == []


def test_traverse_surfaces_multi_hop_evidence(store, tenant_id):
    paths = store.traverse(tenant_id, ["Director Sarah"], max_hops=3, limit=25)
    path_texts = {p["text"] for p in paths}
    assert "Team Alpha reports_to Director Sarah" in path_texts
    # Project Apollo is 2 hops from Director Sarah via Team Alpha -- confirms multi-hop traversal works, not just 1-hop.
    assert any("Project Apollo" in p["text"] for p in paths if p["hops"] >= 2)


def test_upsert_is_idempotent(store, tenant_id):
    """Re-ingesting the same document must not create duplicate entities."""
    store.upsert_graph(tenant_id, TEST_ENTITIES, TEST_RELATIONSHIPS, source_doc="test_doc.md")
    matches = store.find_matching_entities(tenant_id, "Project Apollo", limit=100)
    assert matches.count("Project Apollo") <= 1


def test_tenant_isolation(tenant_id):
    """A different tenant_id must see none of this module's graph data."""
    driver = get_neo4j_driver()
    other_store = GraphStore(driver)
    other_tenant = f"{tenant_id}_other"
    try:
        assert other_store.find_matching_entities(other_tenant, "Director Sarah's team") == []
        assert other_store.traverse(other_tenant, ["Director Sarah"]) == []
    finally:
        other_store.close()
