"""
Tests for server-side conversation memory: the ConversationStore itself
(tenant isolation, ordering, limit) and its wiring into POST /query
(conversation_id round-trip, server-authoritative history once a
conversation_id is passed back). No live LLM/Qdrant needed -- run_agent_v2
is mocked at the API layer.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from artemis.agent.tools.registry import ToolRegistry
from artemis.auth import TenantRagRegistryCache, build_rate_limiter
from artemis.memory import ConversationStore, new_conversation_id


@pytest.fixture
def store(tmp_path):
    return ConversationStore(db_path=str(tmp_path / "conversations.db"))


def test_new_conversation_has_no_history(store):
    assert store.get_history("tenant_a", new_conversation_id()) == []


def test_append_and_get_history_round_trips_in_order(store):
    cid = new_conversation_id()
    store.append_turn("tenant_a", cid, "user", "hello")
    store.append_turn("tenant_a", cid, "assistant", "hi there")
    store.append_turn("tenant_a", cid, "user", "how are you")

    history = store.get_history("tenant_a", cid)
    assert history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
        {"role": "user", "content": "how are you"},
    ]


def test_history_is_isolated_per_tenant(store):
    cid = new_conversation_id()
    store.append_turn("tenant_a", cid, "user", "tenant a's message")
    # Same conversation_id, different tenant -- must not see tenant_a's row.
    assert store.get_history("tenant_b", cid) == []
    assert store.get_history("tenant_a", cid) == [{"role": "user", "content": "tenant a's message"}]


def test_history_is_isolated_per_conversation(store):
    store.append_turn("tenant_a", "conv-1", "user", "first conversation")
    store.append_turn("tenant_a", "conv-2", "user", "second conversation")
    assert store.get_history("tenant_a", "conv-1") == [{"role": "user", "content": "first conversation"}]
    assert store.get_history("tenant_a", "conv-2") == [{"role": "user", "content": "second conversation"}]


def test_get_history_respects_limit(store):
    cid = new_conversation_id()
    for i in range(5):
        store.append_turn("tenant_a", cid, "user", f"message {i}")
    history = store.get_history("tenant_a", cid, limit=2)
    assert history == [{"role": "user", "content": "message 3"}, {"role": "user", "content": "message 4"}]


def test_append_turn_skips_empty_content(store):
    cid = new_conversation_id()
    store.append_turn("tenant_a", cid, "assistant", "")
    assert store.get_history("tenant_a", cid) == []


def test_memory_db_path_persists_across_separate_calls():
    """Regression: each ':memory:' sqlite3.connect() is its own isolated DB --
    a fresh connection per call would silently lose everything from the last call."""
    mem_store = ConversationStore(db_path=":memory:")
    cid = new_conversation_id()
    mem_store.append_turn("tenant_a", cid, "user", "first call")
    mem_store.append_turn("tenant_a", cid, "assistant", "second call")
    assert mem_store.get_history("tenant_a", cid) == [
        {"role": "user", "content": "first call"},
        {"role": "assistant", "content": "second call"},
    ]


@pytest.fixture
def api_client(tmp_path):
    from artemis.api import app

    app.state.config = type("Config", (), {"provider": "groq", "model_name": "x"})()
    app.state.registry = ToolRegistry()
    app.state.rate_limiter = build_rate_limiter()
    app.state.tenant_rag_cache = TenantRagRegistryCache(app.state.config)
    app.state.conversation_store = ConversationStore(db_path=str(tmp_path / "conversations.db"))
    app.state.ready = True
    return TestClient(app)


def _mock_run_agent_v2(query, config=None, registry=None, message_history=None):
    return {"final_answer": "mock answer", "routed_to": "direct", "error": None, "tool_calls": []}


def test_query_without_conversation_id_returns_a_new_one(api_client):
    with patch("artemis.agent.run.run_agent_v2", side_effect=_mock_run_agent_v2):
        response = api_client.post("/query", json={"query": "hello"})
    assert response.status_code == 200
    assert response.json()["conversation_id"]


def test_query_with_conversation_id_loads_server_side_history(api_client):
    store = api_client.app.state.conversation_store
    cid = new_conversation_id()
    store.append_turn("default", cid, "user", "what's my name")
    store.append_turn("default", cid, "assistant", "I don't know yet")

    captured = {}

    def capturing_run_agent_v2(query, config=None, registry=None, message_history=None):
        captured["message_history"] = message_history
        return {"final_answer": "ok", "routed_to": "direct", "error": None, "tool_calls": []}

    with patch("artemis.agent.run.run_agent_v2", side_effect=capturing_run_agent_v2):
        response = api_client.post("/query", json={"query": "it's Alice", "conversation_id": cid})

    assert response.status_code == 200
    assert response.json()["conversation_id"] == cid
    assert captured["message_history"] == [
        {"role": "user", "content": "what's my name"},
        {"role": "assistant", "content": "I don't know yet"},
    ]
    # This turn should now be persisted too.
    assert store.get_history("default", cid)[-2:] == [
        {"role": "user", "content": "it's Alice"},
        {"role": "assistant", "content": "ok"},
    ]


def test_query_with_conversation_id_ignores_client_supplied_message_history(api_client):
    """Once a conversation_id is used, the server's stored history is authoritative."""
    store = api_client.app.state.conversation_store
    cid = new_conversation_id()
    store.append_turn("default", cid, "user", "server-stored message")

    captured = {}

    def capturing_run_agent_v2(query, config=None, registry=None, message_history=None):
        captured["message_history"] = message_history
        return {"final_answer": "ok", "routed_to": "direct", "error": None, "tool_calls": []}

    with patch("artemis.agent.run.run_agent_v2", side_effect=capturing_run_agent_v2):
        api_client.post(
            "/query",
            json={
                "query": "x",
                "conversation_id": cid,
                "message_history": [{"role": "user", "content": "client-supplied, should be ignored"}],
            },
        )

    assert captured["message_history"] == [{"role": "user", "content": "server-stored message"}]
