"""
Web Search Agent prompt: search the public web and answer from results.
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


class WebSearchPrompt(BasePrompt):
    """System and user prompts for the Web Search Agent."""

    def render_system(self, context: dict) -> str:
        """context keys: "tools" (list of {name, description, parameters_schema}), "max_tool_steps" (int)"""
        tools = context.get("tools") or []
        max_tool_steps = context.get("max_tool_steps", 5)

        lines = [
            "You are the Web Search Agent. You answer questions by searching the public web.",
            "",
            "Available tools:",
            _format_tools(tools),
            "",
            "Rules:",
            "1. For questions about current events, recent news, prices, or anything that changes over time or isn't in the knowledge base, call web_search first; do NOT answer direct without search results.",
            '2. After ONE successful search that returned results, use intent="direct" to synthesize an answer citing the source URLs — never call web_search again in the same turn unless the first search returned no useful results.',
            '3. If search returns an error or no results, use intent="direct" to say so plainly rather than guessing an answer.',
            "4. Always cite which result(s) an answer came from (title or URL), since web content can be wrong or outdated.",
            f"5. You have at most {max_tool_steps} tool calls total",
            "",
            JSON_FORMAT_LINE,
        ]
        return "\n".join(lines)
