import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.auth import (
    DEFAULT_TENANT_ID,
    RateLimiter,
    TenantRagRegistryCache,
    parse_api_keys,
    require_api_key,
    scope_registry_to_tenant,
)


def test_parse_api_keys_empty_when_unset(monkeypatch):
    monkeypatch.delenv("ARTEMIS_API_KEYS", raising=False)
    assert parse_api_keys() == {}


def test_parse_api_keys_parses_multiple_entries(monkeypatch):
    monkeypatch.setenv("ARTEMIS_API_KEYS", "key1:tenant_a, key2:tenant_b")
    assert parse_api_keys() == {"key1": "tenant_a", "key2": "tenant_b"}


def test_parse_api_keys_ignores_malformed_entries(monkeypatch):
    monkeypatch.setenv("ARTEMIS_API_KEYS", "key1:tenant_a,not_a_valid_entry,key2:tenant_b")
    assert parse_api_keys() == {"key1": "tenant_a", "key2": "tenant_b"}


@pytest.fixture
def auth_test_app():
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(tenant_id: str = Depends(require_api_key)):
        return {"tenant_id": tenant_id}

    return app


def test_require_api_key_disabled_without_configured_keys(auth_test_app, monkeypatch):
    monkeypatch.delenv("ARTEMIS_API_KEYS", raising=False)
    client = TestClient(auth_test_app)
    response = client.get("/whoami")
    assert response.status_code == 200
    assert response.json()["tenant_id"] == DEFAULT_TENANT_ID


def test_require_api_key_rejects_missing_key(auth_test_app, monkeypatch):
    monkeypatch.setenv("ARTEMIS_API_KEYS", "secret123:tenant_a")
    client = TestClient(auth_test_app)
    response = client.get("/whoami")
    assert response.status_code == 401


def test_require_api_key_rejects_wrong_key(auth_test_app, monkeypatch):
    monkeypatch.setenv("ARTEMIS_API_KEYS", "secret123:tenant_a")
    client = TestClient(auth_test_app)
    response = client.get("/whoami", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_require_api_key_accepts_x_api_key_header(auth_test_app, monkeypatch):
    monkeypatch.setenv("ARTEMIS_API_KEYS", "secret123:tenant_a")
    client = TestClient(auth_test_app)
    response = client.get("/whoami", headers={"X-API-Key": "secret123"})
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant_a"


def test_require_api_key_accepts_bearer_header(auth_test_app, monkeypatch):
    monkeypatch.setenv("ARTEMIS_API_KEYS", "secret123:tenant_a,other456:tenant_b")
    client = TestClient(auth_test_app)
    response = client.get("/whoami", headers={"Authorization": "Bearer other456"})
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant_b"


def _build_fake_collection_registry():
    """A stub registry mimicking the shape build_rag_registry produces, backed by an in-memory dict instead of real Qdrant."""
    store = {}

    registry = ToolRegistry()
    registry.register(
        "list_collections",
        lambda **kw: {"collections": list(store.keys()), "purposes": {k: "p" for k in store}},
        "list",
    )
    registry.register(
        "create_collection",
        lambda **kw: store.setdefault(kw["collection_name"], True) or {"ok": True, "collection_name": kw["collection_name"]},
        "create",
    )
    registry.register(
        "get_collection_info",
        lambda **kw: {"collection_name": kw["collection_name"], "exists": kw["collection_name"] in store},
        "info",
    )
    registry.register(
        "delete_collection",
        lambda **kw: {"ok": bool(store.pop(kw["collection_name"], None))},
        "delete",
    )
    registry.register(
        "search_documents",
        lambda **kw: [{"text": "unaffected by tenant scoping", "score": 1.0, "metadata": {}}],
        "search",
    )
    return registry, store


def test_scope_registry_is_noop_for_default_tenant():
    """Regression test: namespacing the default (auth-disabled) tenant would
    hide pre-existing collections like artemis_system_docs that were never
    created with a prefix."""
    registry, _ = _build_fake_collection_registry()
    assert scope_registry_to_tenant(registry, DEFAULT_TENANT_ID) is registry


def test_scope_registry_prefixes_collection_names():
    registry, store = _build_fake_collection_registry()
    scoped = scope_registry_to_tenant(registry, "tenant_a")

    scoped.get("create_collection").callable(collection_name="notes")

    assert "tenant_a__notes" in store
    assert "notes" not in store


def test_scope_registry_list_collections_shows_only_own_tenant():
    registry, store = _build_fake_collection_registry()
    scoped_a = scope_registry_to_tenant(registry, "tenant_a")
    scoped_b = scope_registry_to_tenant(registry, "tenant_b")

    scoped_a.get("create_collection").callable(collection_name="notes")
    scoped_b.get("create_collection").callable(collection_name="notes")

    result_a = scoped_a.get("list_collections").callable()
    result_b = scoped_b.get("list_collections").callable()

    assert result_a["collections"] == ["notes"]
    assert result_b["collections"] == ["notes"]
    # Two tenants, two distinct real collections, even though the logical name collides
    assert len(store) == 2


def test_scope_registry_tenant_cannot_reach_other_tenants_collection():
    registry, store = _build_fake_collection_registry()
    scoped_a = scope_registry_to_tenant(registry, "tenant_a")
    scoped_b = scope_registry_to_tenant(registry, "tenant_b")

    scoped_a.get("create_collection").callable(collection_name="secret_notes")

    # tenant_b asking for the same logical name hits its own (nonexistent) namespaced collection
    info = scoped_b.get("get_collection_info").callable(collection_name="secret_notes")
    assert info["exists"] is False

    delete_result = scoped_b.get("delete_collection").callable(collection_name="secret_notes")
    assert delete_result["ok"] is False
    assert "tenant_a__secret_notes" in store  # untouched


def test_scope_registry_passes_through_unscoped_tools():
    registry, _ = _build_fake_collection_registry()
    scoped = scope_registry_to_tenant(registry, "tenant_a")
    assert scoped.get("search_documents").callable() == [
        {"text": "unaffected by tenant scoping", "score": 1.0, "metadata": {}}
    ]


def test_rate_limiter_allows_up_to_the_limit_then_blocks():
    limiter = RateLimiter(max_requests=2, window_seconds=60.0)
    limiter.check("tenant_a")
    limiter.check("tenant_a")
    with pytest.raises(Exception):
        limiter.check("tenant_a")


def test_rate_limiter_tracks_tenants_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60.0)
    limiter.check("tenant_a")
    limiter.check("tenant_b")  # different tenant, independent budget -- should not raise


class _FakeEmbedder:
    """Stands in for the real sentence-transformers model: registry construction
    never calls encode()/get_dimension(), only Retriever/Indexer __init__ wiring."""


@pytest.fixture
def fake_config(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")  # unreachable is fine; construction is lazy
    return AgentConfig(provider="groq", model_name="x", retrieval_k=5, groq_api_key="fake-key")


def test_tenant_rag_cache_is_noop_for_default_tenant(fake_config):
    cache = TenantRagRegistryCache(fake_config)
    default_registry = ToolRegistry()
    assert cache.get(DEFAULT_TENANT_ID, default_registry) is default_registry


def test_tenant_rag_cache_builds_distinct_isolated_registries(fake_config, monkeypatch):
    monkeypatch.setattr("artemis.rag.core.embedder.Embedder", _FakeEmbedder)
    cache = TenantRagRegistryCache(fake_config)
    default_registry = ToolRegistry()

    registry_a = cache.get("tenant_a", default_registry)
    registry_b = cache.get("tenant_b", default_registry)

    assert registry_a is not registry_b
    assert "search_documents" in [t["name"] for t in registry_a.list_tools()]

    schema_a = registry_a.get("search_documents").parameters_schema
    schema_b = registry_b.get("search_documents").parameters_schema
    default_coll_a = schema_a["properties"]["collection_name"]["default"]
    default_coll_b = schema_b["properties"]["collection_name"]["default"]
    assert default_coll_a == "tenant_a__artemis_user_docs"
    assert default_coll_b == "tenant_b__artemis_user_docs"
    assert default_coll_a != default_coll_b


def test_tenant_rag_cache_reuses_registry_on_repeat_calls(fake_config, monkeypatch):
    monkeypatch.setattr("artemis.rag.core.embedder.Embedder", _FakeEmbedder)
    cache = TenantRagRegistryCache(fake_config)
    default_registry = ToolRegistry()

    first = cache.get("tenant_a", default_registry)
    second = cache.get("tenant_a", default_registry)
    assert first is second
