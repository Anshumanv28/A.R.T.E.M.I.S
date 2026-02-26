"""
Ingestion Agent prompt: add data to the knowledge base.
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


class IngestionPrompt(BasePrompt):
    """System and user prompts for the Ingestion Agent."""

    def render_system(self, context: dict) -> str:
        """
        context keys: "chunk_strategies" (list), "csv_schemas" (list), "collections" (list),
                      "default_collection" (str), "tools" (list), "max_tool_steps" (int)
        """
        chunk_strategies = context.get("chunk_strategies") or []
        csv_schemas = context.get("csv_schemas") or []
        collections = context.get("collections") or []
        default_collection = context.get("default_collection") or ""
        tools = context.get("tools") or []

        lines = [
            "You are the Ingestion Agent. You add data to the knowledge base.",
            "",
            "Available chunk strategies:",
        ]
        if chunk_strategies:
            lines.append(", ".join(str(s) for s in chunk_strategies))
        else:
            lines.append("defaults will be chosen automatically")
        lines.append("")
        lines.append("Available CSV schemas:")
        if csv_schemas:
            lines.append(", ".join(str(s) for s in csv_schemas))
        else:
            lines.append("none")
        lines.append("")
        lines.append("Available collections:")
        if collections:
            for c in collections:
                mark = " (default)" if c == default_collection else ""
                lines.append(f"- {c}{mark}")
        else:
            lines.append("(none)")
        lines.append("")
        lines.append("Available tools:")
        lines.append(_format_tools(tools))
        lines.append("")
        lines.append("Rules — FOLLOW IN ORDER:")
        lines.append("1. When given a file or directory path: ALWAYS call suggest_ingest_options FIRST with the path. Do not skip this step.")
        lines.append("2. Read the returned file_type, chunk_strategy, chunk_size, overlap, and schema from the suggest_ingest_options result")
        lines.append("3. Use those exact values when calling ingest_file (for a file) or ingest_directory (for a directory)")
        lines.append("4. After a successful ingest (ok=True, ingested_count > 0), use intent=\"direct\" to confirm — report the ingested_count to the user")
        lines.append("5. Do NOT call ingest_file or ingest_directory again for the same path in the same session")
        lines.append(f"6. If no collection is specified, use {default_collection or 'the default collection'}")
        lines.append("")
        lines.append(JSON_FORMAT_LINE)
        return "\n".join(lines)
