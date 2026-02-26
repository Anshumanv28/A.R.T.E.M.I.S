"""
Collection Management Agent prompt: manage Qdrant collections.
"""

from typing import Any, Dict, List

from artemis.agent.prompts.base import BasePrompt

JSON_FORMAT_LINE = (
    'Respond with ONLY a JSON object in this exact format (no markdown, no extra text): '
    '{"intent": "tool" or "direct", "tool_name": "<name>" (only if intent is tool), '
    '"tool_args": {} (only if intent is tool, with the right parameters), '
    '"confidence": 0.0-1.0, "reasoning": "brief explanation"}'
)


def _format_tools(tools: List[Dict[str, Any]]) -> str:
    """Format tools list as name + description."""
    if not tools:
        return "(No tools registered)"
    lines = []
    for t in tools:
        name = t.get("name", "?")
        desc = t.get("description", "")
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


class CollectionManagementPrompt(BasePrompt):
    """System and user prompts for the Collection Management Agent."""

    def render_system(self, context: dict) -> str:
        """
        context keys: "collections" (list), "collection_info" (dict), "tools" (list), "max_tool_steps" (int)
        """
        collections = context.get("collections") or []
        collection_info = context.get("collection_info") or {}
        tools = context.get("tools") or []
        max_tool_steps = context.get("max_tool_steps", 10)

        lines = [
            "You are the Collection Management Agent. You manage Qdrant collections.",
            "",
            "Current collections:",
        ]
        if not collections:
            lines.append("(none)")
        else:
            for c in collections:
                info = collection_info.get(c) if isinstance(collection_info, dict) else {}
                points = (
                    info.get("points_count", info.get("points", "unknown"))
                    if isinstance(info, dict)
                    else "unknown"
                )
                lines.append(f"- {c}: {points} points")
        lines.append("")
        lines.append("Available tools:")
        lines.append(_format_tools(tools))
        lines.append("")
        lines.append("Rules:")
        lines.append(
            '1. For clear_collection or delete_collection: only set confirm=True if the user has explicitly said "yes", "confirm", "go ahead", "delete it", or equivalent in their message. If not explicit, use intent="direct" to ask for confirmation first.'
        )
        lines.append("2. Never infer confirmation. Explicit = user used a confirmation word in this exact query.")
        lines.append("3. Use get_collection_info to check state before any destructive operation")
        lines.append(f"4. You have at most {max_tool_steps} tool calls")
        lines.append("")
        lines.append(JSON_FORMAT_LINE)
        return "\n".join(lines)
