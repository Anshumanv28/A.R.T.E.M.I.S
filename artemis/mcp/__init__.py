"""
MCP server exposing the artemis ToolRegistry, scoped by least-privilege tool allow-lists.
"""

from artemis.mcp.scopes import MCP_SCOPES, DEFAULT_SCOPE
from artemis.mcp.server import build_server

__all__ = ["build_server", "MCP_SCOPES", "DEFAULT_SCOPE"]
