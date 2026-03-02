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
        lines.append("0. When the user asks about options or best practices WITHOUT specifying a path (e.g. 'best options for a PDF?', 'what chunking for markdown?'): use get_rag_options and answer from that—do NOT call suggest_ingest_options (it requires an existing file/directory path).")
        lines.append("0a. When the user asks what folders/directories exist, project layout, or what they can ingest WITHOUT naming a path (e.g. 'what folders are there?', 'list directories', 'project structure'): call list_directory with path '.' to list the current directory, then use intent=\"direct\" to answer from the returned directories and files.")
        lines.append("0b. When the user asks only to DISCOVER, EXPLORE, or LIST what is in a path (e.g. 'discover the docs folder', 'what's in docs?', 'can you discover /docs?') and does NOT say ingest/add: call suggest_ingest_options with that path, then use intent=\"direct\" to report what is there (file count, types, recommended options). Do NOT call ingest_file or ingest_directory.")
        lines.append("1. Use the EXACT path or directory the user gave. Do NOT substitute a different path (e.g. if the user said 'docs' use 'docs', not 'RAG_demo' or anything else). When the user asks to ingest the project's 'docs' folder (system/project documentation), use collection_name artemis_system_docs so system docs go into the system collection; for other user content use artemis_user_docs.")
        lines.append("2. When the user explicitly asks to INGEST a path: call suggest_ingest_options FIRST with that exact path, then call ingest_file or ingest_directory. When they only asked to discover/explore/list, stop after suggest_ingest_options and answer.")
        lines.append("3. Read the returned file_type, chunk_strategy, chunk_size, overlap, and schema from the suggest_ingest_options result")
        lines.append("4. Use those exact values when calling ingest_file (for a file) or ingest_directory (for a directory). For ingest_file, set path to the exact file path from suggest_ingest_options (e.g. result.path) or the user (e.g. 'README.md')—never '.' or ''. For ingest_directory, set directory_path to the SAME path you passed to suggest_ingest_options (e.g. if the user said 'docs' or '/docs' or 'the docs folder', pass directory_path 'docs'). Never use '.' or '' for path or directory_path unless the user explicitly asked to ingest the current directory.")
        lines.append("5. After a successful ingest (ok=True, ingested_count > 0), use intent=\"direct\" to confirm — report the ingested_count to the user")
        lines.append("6. Do NOT call ingest_file or ingest_directory again for the same path in the same session")
        lines.append(f"7. If no collection is specified, use {default_collection or 'the default collection'} or a collection name from list_collections (call list_collections to see available names). Use only artemis_system_docs or artemis_user_docs for collection_name when ingesting (these are the only supported names).")
        lines.append("8. When ingest_file or ingest_directory reports that the collection is not available: call create_collection with that collection name (use artemis_system_docs for system docs, artemis_user_docs for user content), then retry the ingest. Do not just report failure—create the collection and proceed.")
        lines.append("")
        lines.append(JSON_FORMAT_LINE)
        return "\n".join(lines)
