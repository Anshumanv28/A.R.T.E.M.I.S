"""
Low-level MCP server over an artemis ToolRegistry: list_tools/call_tool handlers
are data-driven over the registry rather than one decorated function per tool,
matching the registry's own plain-function style.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from artemis.agent.tools.registry import ToolRegistry
from artemis.mcp.adapter import call_tool_safely, descriptor_to_mcp_tool
from artemis.utils import get_logger

logger = get_logger(__name__)


def build_server(registry: ToolRegistry, name: str = "artemis") -> Server:
    """Build (but do not run) an MCP Server exposing every tool in `registry`."""
    server = Server(name)

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            descriptor_to_mcp_tool(registry.get(meta["name"]))
            for meta in registry.list_tools()
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        return call_tool_safely(registry, name, arguments)

    return server


async def run_stdio(registry: ToolRegistry, name: str = "artemis") -> None:
    """Run an MCP server over stdio until the client disconnects."""
    server = build_server(registry, name=name)
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server %r running over stdio", name)
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


__all__ = ["build_server", "run_stdio"]
