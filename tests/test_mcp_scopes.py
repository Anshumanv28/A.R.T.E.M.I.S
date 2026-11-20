"""
MCP_SCOPES is the least-privilege access model for the MCP server --
each scope maps to a tool allow-list reused verbatim from the matching
sub-agent (see artemis/mcp/scopes.py). No live MCP transport needed to
test this: it's a static dict plus the existing _filter_registry helper.
"""

from artemis.agent.agents.base import _filter_registry
from artemis.agent.agents.web_search_agent import WEB_SEARCH_AGENT_TOOLS
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.tools.web_search import register_web_search_tool
from artemis.mcp.scopes import DEFAULT_SCOPE, MCP_SCOPES


def test_web_search_scope_matches_the_sub_agent_allow_list():
    assert MCP_SCOPES["web_search"] == WEB_SEARCH_AGENT_TOOLS


def test_every_named_scope_has_a_non_empty_allow_list():
    for name, tools in MCP_SCOPES.items():
        if name == "full":
            assert tools is None  # "full" means no filtering
        else:
            assert tools, f"scope {name!r} has an empty tool allow-list"


def test_default_scope_is_a_real_scope():
    assert DEFAULT_SCOPE in MCP_SCOPES


def test_web_search_scope_filters_registry_to_just_that_tool():
    registry = ToolRegistry()
    register_web_search_tool(registry, api_key="fake-key")
    registry.register("search_documents", lambda **kw: [], "unrelated rag tool")
    registry.register("create_collection", lambda **kw: {}, "unrelated collection tool")

    scoped = _filter_registry(registry, MCP_SCOPES["web_search"])

    assert [t["name"] for t in scoped.list_tools()] == ["web_search"]


def test_web_search_scope_is_empty_when_tool_not_registered():
    """TAVILY_API_KEY not set -> web_search was never registered -> scope filters to nothing, not an error."""
    registry = ToolRegistry()
    registry.register("search_documents", lambda **kw: [], "unrelated rag tool")

    scoped = _filter_registry(registry, MCP_SCOPES["web_search"])

    assert scoped.list_tools() == []
