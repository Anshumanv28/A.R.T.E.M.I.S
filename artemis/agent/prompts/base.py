"""
Base prompt interface for agent system and user prompts.
"""


class BasePrompt:
    """Base class for system and user prompt rendering."""

    def render_system(self, context: dict) -> str:
        """Build the system prompt from the given context. Subclasses must implement."""
        raise NotImplementedError

    def render_user(
        self,
        query: str,
        tool_calls: list,
        prior_context: str = "",
    ) -> str:
        """
        Build the user prompt. Default: same format as existing planner user prompt.
        prior_context is the formatted prior tool results string (can be empty).
        """
        return f"Query: {query}{prior_context}\n\nClassify intent and respond with JSON only."
