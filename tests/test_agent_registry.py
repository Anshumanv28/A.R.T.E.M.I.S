"""
Unit tests for the agent tool registry, tool_node, and build_rag_registry.
No real LLM or Qdrant required.
"""

import pytest

from artemis.agent.tools import ToolRegistry, ToolDescriptor, build_rag_registry
from artemis.agent.nodes.tool_node import tool_node
from artemis.agent.state import AgentState


# --- ToolRegistry ---


def test_registry_register_and_list_tools():
    """Register a tool; list_tools returns one entry with name, description, schema; no callable."""
    registry = ToolRegistry()
    def fn(**kwargs):
        return kwargs.get("x", 0)
    registry.register("my_tool", fn, "Does something", {"type": "object", "properties": {"x": {"type": "integer"}}})
    listed = registry.list_tools()
    assert len(listed) == 1
    assert listed[0]["name"] == "my_tool"
    assert listed[0]["description"] == "Does something"
    assert listed[0]["parameters_schema"] == {"type": "object", "properties": {"x": {"type": "integer"}}}
    assert "callable" not in listed[0]


def test_registry_get_returns_descriptor_and_callable_works():
    """get(name) returns a descriptor whose callable runs and returns the expected value."""
    registry = ToolRegistry()
    registry.register("echo", lambda **kw: kw.get("value", ""), "Echo", None)
    desc = registry.get("echo")
    assert isinstance(desc, ToolDescriptor)
    assert desc.name == "echo"
    assert desc.callable(value="hello") == "hello"


def test_registry_register_same_name_raises():
    """Registering the same name again raises ValueError."""
    registry = ToolRegistry()
    registry.register("dup", lambda: None, "Desc", None)
    with pytest.raises(ValueError, match="already registered"):
        registry.register("dup", lambda: None, "Other", None)


def test_registry_get_unknown_raises():
    """get('unknown') raises KeyError."""
    registry = ToolRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.get("unknown")


# --- tool_node ---


def test_tool_node_appends_result_and_increments_step_count():
    """After tool_node: tool_calls has one item with result, ok True; step_count 1; tool_calls_summary set."""
    registry = ToolRegistry()
    registry.register("my_tool", lambda **kw: "ok", "Tool", None)
    state: AgentState = {
        "query": "q",
        "tool_name": "my_tool",
        "tool_args": {"x": 1},
        "tool_calls": [],
        "step_count": 0,
    }
    out = tool_node(state, registry)
    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["tool_name"] == "my_tool"
    assert out["tool_calls"][0]["arguments"] == {"x": 1}
    assert out["tool_calls"][0]["result"] == "ok"
    assert out["tool_calls"][0]["ok"] is True
    assert out["step_count"] == 1
    assert out.get("tool_calls_summary")


def test_tool_node_tool_raises_sets_ok_false():
    """Tool that raises: result is the error string, ok is False."""
    registry = ToolRegistry()
    def fail(**kw):
        raise ValueError("tool failed")
    registry.register("bad", fail, "Bad", None)
    state: AgentState = {
        "query": "q",
        "tool_name": "bad",
        "tool_args": {},
        "tool_calls": [],
        "step_count": 0,
    }
    out = tool_node(state, registry)
    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["ok"] is False
    assert "tool failed" in str(out["tool_calls"][0]["result"])
    assert out["step_count"] == 1


def test_tool_node_missing_tool_name_sets_error():
    """Missing tool_name: state gets error and no new tool_calls entry."""
    registry = ToolRegistry()
    state: AgentState = {
        "query": "q",
        "tool_name": None,
        "tool_args": {},
        "tool_calls": [],
        "step_count": 0,
    }
    out = tool_node(state, registry)
    assert out.get("error")
    assert "missing tool_name" in (out.get("error") or "")
    assert len(out.get("tool_calls", [])) == 0


def test_tool_node_unknown_tool_appends_ok_false():
    """Unknown tool name: append to tool_calls with ok False, result is KeyError message."""
    registry = ToolRegistry()
    state: AgentState = {
        "query": "q",
        "tool_name": "nonexistent",
        "tool_args": {},
        "tool_calls": [],
        "step_count": 0,
    }
    out = tool_node(state, registry)
    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["tool_name"] == "nonexistent"
    assert out["tool_calls"][0]["ok"] is False
    assert "not registered" in str(out["tool_calls"][0]["result"])
    assert out["step_count"] == 1


# --- build_rag_registry ---


def test_build_rag_registry_includes_search_documents(mock_retriever):
    """build_rag_registry(mock_retriever) list_tools includes search_documents."""
    registry = build_rag_registry(mock_retriever, indexer=None, default_k=5)
    names = [t["name"] for t in registry.list_tools()]
    assert "search_documents" in names


def test_build_rag_registry_search_documents_calls_retriever(mock_retriever):
    """Calling the registered search_documents with query='test' calls retriever.retrieve and returns result."""
    registry = build_rag_registry(mock_retriever, indexer=None, default_k=5)
    desc = registry.get("search_documents")
    result = desc.callable(query="test")
    assert mock_retriever.retrieve_calls == [("test", 5)]
    assert result == mock_retriever.docs


def test_build_rag_registry_search_documents_respects_k(mock_retriever):
    """search_documents with k=2 calls retriever with k=2."""
    registry = build_rag_registry(mock_retriever, indexer=None, default_k=5)
    desc = registry.get("search_documents")
    desc.callable(query="q", k=2)
    assert mock_retriever.retrieve_calls == [("q", 2)]
