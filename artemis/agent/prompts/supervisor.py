"""
Supervisor prompt: route user query to the correct agent.
"""

from artemis.agent.prompts.base import BasePrompt


class SupervisorPrompt(BasePrompt):
    """System and user prompts for the ARTEMIS Supervisor (routing)."""

    def render_system(self, context: dict) -> str:
        """
        context keys: "agents" (list of {name, description}), "collections" (list of str),
                      "last_routed_to" (optional str): agent used in the previous turn.
        Produce a system prompt for routing to the correct agent.
        """
        agents = context.get("agents") or []
        collections = context.get("collections") or []
        last_routed_to = context.get("last_routed_to")
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
        if last_routed_to and last_routed_to in agent_names:
            lines.append("")
            lines.append(
                f"Last turn was routed to: {last_routed_to}. When the user says 'try again', 'do it', "
                "'yes', 'yes run it', 'go ahead', 'do that', or similar follow-up, route to that same "
                f"agent ({last_routed_to}) so it can actually call the tool—do NOT use direct."
            )
        lines.append("")
        lines.append("Routing rules:")
        lines.append(
            '- Use "direct" when the user message is ONLY an acknowledgment, affirmation, or short social reply—e.g. "that\'s great", "sounds good", "ok", "perfect", "got it", "thanks", "cool", "good", "understood", "noted", "great", "awesome", "nice", "alright", or greetings like "hi", "hello". No sub-agent or tools needed; just reply briefly.'
        )
        lines.append(
            '- Use "direct" for thanks, greetings, or off-topic chat. Do NOT use direct for follow-ups like "try again" or "yes run it" (route to the same agent as last turn).'
        )
        lines.append("- When the user asks to check if a file or folder exists, list directory contents, or discover the filesystem (e.g. 'is there a readme', 'list files at root'), route to ingestion—do NOT use direct.")
        lines.append("- When the user asks which collections exist or about Qdrant collections, route to collection_management.")
        lines.append(
            "- Only route to rag_search, ingestion, or collection_management when the user is asking a question, requesting an action (search, ingest, create collection), or needs information from a tool. Short acknowledgments and affirmations always go to direct."
        )
        lines.append("")
        valid = ", ".join(agent_names)
        lines.append(
            'Respond with ONLY a JSON object: {"agent": "<name>", "reasoning": "<brief>"}'
        )
        lines.append(f"Valid agent names are exactly: {valid}.")
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
