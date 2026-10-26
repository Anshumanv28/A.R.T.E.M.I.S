"""
Translation between artemis's ToolRegistry/ToolDescriptor and MCP's Tool/content types.
"""

import json
from typing import Any, Dict, List

import mcp.types as types

from artemis.agent.tools.registry import ToolDescriptor, ToolRegistry
from artemis.utils import get_logger

logger = get_logger(__name__)


def descriptor_to_mcp_tool(descriptor: ToolDescriptor) -> types.Tool:
    """Translate a ToolDescriptor into an MCP Tool (parameters_schema -> inputSchema)."""
    return types.Tool(
        name=descriptor.name,
        description=descriptor.description,
        inputSchema=descriptor.parameters_schema or {"type": "object", "properties": {}},
    )


def call_tool_safely(
    registry: ToolRegistry, name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """
    Invoke a tool by name against the (already scope-filtered) registry.

    Returns a single TextContent either way so the MCP client always gets a readable
    result rather than a transport-level error: unknown/out-of-scope tool names and
    tool-execution exceptions are both reported as text, not raised.
    """
    try:
        descriptor = registry.get(name)
    except KeyError:
        logger.warning("MCP call_tool: unknown or out-of-scope tool %r", name)
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    try:
        result = descriptor.callable(**arguments)
    except Exception as e:
        logger.exception("MCP call_tool: tool %r raised", name)
        return [types.TextContent(type="text", text=f"Tool {name} failed: {e}")]

    if isinstance(result, str):
        text = result
    else:
        text = json.dumps(result, default=str, indent=2)
    return [types.TextContent(type="text", text=text)]


__all__ = ["descriptor_to_mcp_tool", "call_tool_safely"]
