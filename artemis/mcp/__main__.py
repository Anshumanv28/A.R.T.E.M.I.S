"""
Run the artemis MCP server over stdio: python -m artemis.mcp --scope rag_search
"""

import argparse
import asyncio
import sys

from artemis.agent.agents.base import _filter_registry
from artemis.agent.run import get_v2_runtime
from artemis.mcp.scopes import DEFAULT_SCOPE, MCP_SCOPES
from artemis.mcp.server import run_stdio
from artemis.utils import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m artemis.mcp")
    parser.add_argument(
        "--scope",
        choices=sorted(MCP_SCOPES.keys()),
        default=DEFAULT_SCOPE,
        help=f"Tool scope to expose (default: {DEFAULT_SCOPE}).",
    )
    args = parser.parse_args()

    tool_names = MCP_SCOPES[args.scope]
    _config, registry = get_v2_runtime()
    if tool_names is not None:
        registry = _filter_registry(registry, tool_names)

    logger.info("Starting artemis MCP server (scope=%s)", args.scope)
    try:
        asyncio.run(run_stdio(registry, name=f"artemis-{args.scope}"))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main() or 0)
