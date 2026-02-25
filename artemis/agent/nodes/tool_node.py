"""
Tool execution node.

Runs the tool selected by the planner (from state), appends result to tool_calls
with ok flag, increments step_count, and returns state for the next planner step.
"""

from typing import Any, Dict

from artemis.agent.state import AgentState
from artemis.agent.tools.registry import ToolRegistry
from artemis.utils import get_logger

logger = get_logger(__name__)


def _summarize_tool_call(tool_name: str, arguments: Dict[str, Any], result: Any, ok: bool) -> str:
    """Build a short one-line summary of a single tool call for state or prompt."""
    status = "ok" if ok else "error"
    if ok:
        if isinstance(result, list):
            return f"{tool_name}(...): {status}, {len(result)} items"
        if isinstance(result, dict):
            return f"{tool_name}(...): {status}, keys={list(result.keys())[:5]}"
        return f"{tool_name}(...): {status}"
    err = str(result) if result else "unknown"
    return f"{tool_name}(...): {status}, {err[:80]}"


def tool_node(state: AgentState, registry: ToolRegistry) -> AgentState:
    """
    Execute the tool indicated by state (tool_name, tool_args), append to tool_calls, increment step_count.

    Each tool_calls entry is {"tool_name", "arguments", "result", "ok": bool}.
    On exception, result is the error message and ok=False.
    Updates tool_calls_summary with a short summary of all tool calls for direct_answer.
    """
    tool_name = state.get("tool_name")
    tool_args = state.get("tool_args") or {}
    tool_calls = list(state.get("tool_calls") or [])
    step_count = state.get("step_count", 0)

    if not tool_name:
        logger.warning("Tool node called without tool_name; returning state unchanged")
        return {**state, "error": "Tool node: missing tool_name"}

    try:
        descriptor = registry.get(tool_name)
    except KeyError as e:
        logger.warning(f"Tool not found: {tool_name}")
        tool_calls.append({
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": str(e),
            "ok": False,
        })
        step_count += 1
        summary_lines = [ _summarize_tool_call(t["tool_name"], t["arguments"], t["result"], t["ok"]) for t in tool_calls ]
        return {
            **state,
            "tool_calls": tool_calls,
            "step_count": step_count,
            "tool_calls_summary": "\n".join(summary_lines),
        }

    try:
        result = descriptor.callable(**tool_args)
        ok = True
        if tool_name == "search_documents" and isinstance(result, list) and len(result) == 0:
            logger.info("search_documents returned 0 results (empty collection or no matching documents)")
    except Exception as e:
        logger.exception(f"Tool {tool_name} failed: {e}")
        result = str(e)
        ok = False

    tool_calls.append({
        "tool_name": tool_name,
        "arguments": tool_args,
        "result": result,
        "ok": ok,
    })
    step_count += 1
    summary_lines = [_summarize_tool_call(t["tool_name"], t["arguments"], t["result"], t["ok"]) for t in tool_calls]
    return {
        **state,
        "tool_calls": tool_calls,
        "step_count": step_count,
        "tool_calls_summary": "\n".join(summary_lines),
    }
