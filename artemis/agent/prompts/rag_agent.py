"""
RAG Search Agent prompt: search the knowledge base and answer from results.
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


class RAGSearchPrompt(BasePrompt):
    """System and user prompts for the RAG Search Agent."""

    def render_system(self, context: dict) -> str:
        """
        context keys: "collections" (list), "collection_info" (dict), "search_modes" (list),
                      "tools" (list of {name, description, parameters_schema}),
                      "max_tool_steps" (int)
        """
        collections = context.get("collections") or []
        collection_info = context.get("collection_info") or {}
        search_modes = context.get("search_modes") or ["semantic"]
        tools = context.get("tools") or []
        max_tool_steps = context.get("max_tool_steps", 10)

        lines = [
            "You are the RAG Search Agent. You answer questions by searching the knowledge base.",
            "",
            "Available collections:",
        ]
        if not collections:
            lines.append("No collections loaded.")
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
        lines.append("Available search modes: " + ", ".join(str(m) for m in search_modes))
        lines.append("")
        lines.append("Available tools:")
        lines.append(_format_tools(tools))
        lines.append("")
        lines.append("Rules:")
        lines.append("1. For questions about 'ingested content', 'main topic', 'what documents are there', or 'summarize'—call search_documents first; do NOT answer direct without search results.")
        lines.append("2. Call search_documents with the most relevant collection_name for the query")
        lines.append(
            '3. After ONE successful search that returned results, use intent="direct" to synthesize — never call search_documents again in the same session'
        )
        lines.append('4. If search returns empty results, use intent="direct" to say no results found')
        lines.append("5. Use list_collections or get_collection_info only when the user asks about collection state")
        lines.append(f"6. You have at most {max_tool_steps} tool calls total")
        lines.append("")
        lines.append(JSON_FORMAT_LINE)
        return "\n".join(lines)
