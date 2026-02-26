"""
Supervisor prompt: route user query to the correct agent.
"""

from artemis.agent.prompts.base import BasePrompt


class SupervisorPrompt(BasePrompt):
    """System and user prompts for the ARTEMIS Supervisor (routing)."""

    def render_system(self, context: dict) -> str:
        """
        context keys: "agents" (list of {name, description}), "collections" (list of str).
        Produce a system prompt for routing to the correct agent.
        """
        agents = context.get("agents") or []
        collections = context.get("collections") or []
        agent_names = ["direct"]
        lines = [
            "You are the ARTEMIS Supervisor. Route the user query to the correct agent.",
            "",
            "Agents:",
        ]
        for a in agents:
            name = a.get("name") if isinstance(a, dict) else None
            desc = a.get("description", "") if isinstance(a, dict) else ""
            if name:
                agent_names.append(str(name))
                lines.append(f"- {name}: {desc}")
        lines.append("")
        if collections:
            lines.append("Available collections: " + ", ".join(str(c) for c in collections))
        else:
            lines.append("Available collections: none loaded")
        lines.append("")
        valid = ", ".join(agent_names)
        lines.append(
            'Respond with ONLY a JSON object: {"agent": "<name>", "reasoning": "<brief>"}'
        )
        lines.append(f"Valid agent names are exactly: {valid}.")
        lines.append(
            'Use "direct" for greetings, thanks, unclear queries, or questions answerable without tools.'
        )
        lines.append("No markdown, no extra text — JSON only.")
        return "\n".join(lines)

    def render_user(
        self,
        query: str,
        tool_calls: list = None,
        prior_context: str = "",
        **kwargs,
    ) -> str:
        """User prompt for supervisor: route to the correct agent. Override, do not inherit base."""
        return f"Query: {query}\n\nRoute to the correct agent. Respond with JSON only."
