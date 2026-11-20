"""
Tests for the web_search tool (Tavily-backed) and its optional wiring into
the registry/Supervisor. No real network calls -- requests.post is mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from artemis.agent.agents import WEB_SEARCH_AGENT_TOOLS, build_web_search_agent
from artemis.agent.config import AgentConfig
from artemis.agent.supervisor import Supervisor
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.tools.web_search import register_web_search_tool, web_search


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        import requests
        resp.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
    else:
        resp.raise_for_status.side_effect = None
    return resp


def test_web_search_returns_formatted_results():
    tavily_payload = {
        "results": [
            {"title": "Result A", "url": "https://a.example", "content": "text a", "score": 0.9},
            {"title": "Result B", "url": "https://b.example", "content": "text b", "score": 0.5},
        ]
    }
    with patch("artemis.agent.tools.web_search.requests.post", return_value=_mock_response(tavily_payload)) as mock_post:
        results = web_search("who won the game", api_key="fake-key", max_results=2)

    assert results == [
        {"title": "Result A", "url": "https://a.example", "content": "text a", "score": 0.9},
        {"title": "Result B", "url": "https://b.example", "content": "text b", "score": 0.5},
    ]
    sent_json = mock_post.call_args.kwargs["json"]
    assert sent_json["api_key"] == "fake-key"
    assert sent_json["query"] == "who won the game"
    assert sent_json["max_results"] == 2


def test_web_search_truncates_to_max_results():
    tavily_payload = {"results": [{"title": f"R{i}", "url": "u", "content": "c", "score": 1.0} for i in range(5)]}
    with patch("artemis.agent.tools.web_search.requests.post", return_value=_mock_response(tavily_payload)):
        results = web_search("x", api_key="fake-key", max_results=2)
    assert len(results) == 2


def test_web_search_returns_error_entry_on_request_failure():
    import requests

    with patch("artemis.agent.tools.web_search.requests.post", side_effect=requests.ConnectionError("boom")):
        results = web_search("x", api_key="fake-key")
    assert len(results) == 1
    assert "error" in results[0]


def test_web_search_returns_error_entry_on_http_error():
    with patch("artemis.agent.tools.web_search.requests.post", return_value=_mock_response({}, status_code=401)):
        results = web_search("x", api_key="bad-key")
    assert len(results) == 1
    assert "error" in results[0]


def test_register_web_search_tool_dispatches_through_registry():
    registry = ToolRegistry()
    tavily_payload = {"results": [{"title": "T", "url": "u", "content": "c", "score": 1.0}]}
    with patch("artemis.agent.tools.web_search.requests.post", return_value=_mock_response(tavily_payload)):
        register_web_search_tool(registry, api_key="fake-key")
        result = registry.get("web_search").callable(query="hello")
    assert result[0]["title"] == "T"


def test_build_web_search_agent_only_has_web_search_tool():
    registry = ToolRegistry()
    register_web_search_tool(registry, api_key="fake-key")
    registry.register("search_documents", lambda **kw: [], "unrelated rag tool")  # should be filtered out

    config = AgentConfig(provider="groq", groq_api_key="fake")
    from artemis.agent.context import SystemContext

    system_context = SystemContext(collections=[], collection_info={}, search_modes=[], chunk_strategies=[], csv_schemas=[])
    agent = build_web_search_agent(config, registry, system_context)

    tool_names = [t["name"] for t in agent.registry.list_tools()]
    assert tool_names == ["web_search"]
    assert WEB_SEARCH_AGENT_TOOLS == ["web_search"]


def test_supervisor_does_not_expose_web_search_without_the_tool():
    config = AgentConfig(provider="groq", groq_api_key="fake")
    registry = ToolRegistry()  # no web_search tool registered
    supervisor = Supervisor(config=config, registry=registry)
    assert "web_search" not in supervisor.agent_descriptions
    assert "web_search" not in supervisor._agent_names


def test_supervisor_exposes_web_search_when_tool_is_present():
    config = AgentConfig(provider="groq", groq_api_key="fake")
    registry = ToolRegistry()
    register_web_search_tool(registry, api_key="fake-key")
    supervisor = Supervisor(config=config, registry=registry)
    assert "web_search" in supervisor.agent_descriptions
    assert "web_search" in supervisor._agent_names


def test_maybe_register_web_search_skips_without_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    from artemis.agent.run import _maybe_register_web_search

    config = AgentConfig(provider="groq", groq_api_key="fake", tavily_api_key=None)
    registry = ToolRegistry()
    _maybe_register_web_search(registry, config)
    with pytest.raises(KeyError):
        registry.get("web_search")


def test_maybe_register_web_search_registers_with_key():
    from artemis.agent.run import _maybe_register_web_search

    config = AgentConfig(provider="groq", groq_api_key="fake", tavily_api_key="fake-tavily-key")
    registry = ToolRegistry()
    _maybe_register_web_search(registry, config)
    assert registry.get("web_search") is not None
