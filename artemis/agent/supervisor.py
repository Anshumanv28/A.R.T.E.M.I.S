"""
Supervisor: routes user queries to the correct sub-agent via a single LLM call.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, Dict, Optional

from artemis.agent.config import AgentConfig
from artemis.agent.context import SystemContext, load_system_context
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.agent.nodes.direct_answer import direct_answer_node
from artemis.agent.prompts.supervisor import SupervisorPrompt
from artemis.agent.state import AgentState
from artemis.agent.tools.registry import ToolRegistry
from artemis.utils import get_logger

if TYPE_CHECKING:
    from artemis.agent.agents.base import SubAgentGraph

logger = get_logger(__name__)


class Supervisor:
    """
    Routes user queries to the correct sub-agent via a single lightweight LLM call.
    No tool loop — just classify then dispatch. Extensible: call register_agent()
    to add new agents (browser, web search, etc.).
    """

    DEFAULT_AGENT_DESCRIPTIONS: Dict[str, str] = {
        "rag_search": "Search the knowledge base and answer from results.",
        "ingestion": "Discover filesystem (list directory, check if file/folder exists), suggest ingest options, and add data to the knowledge base (ingest documents).",
        "collection_management": "Manage Qdrant collections (create, delete, list).",
    }

    def __init__(
        self,
        config: AgentConfig,
        registry: ToolRegistry,
        system_context: Optional[SystemContext] = None,
        agents: Optional[Dict[str, SubAgentGraph]] = None,
        agent_descriptions: Optional[Dict[str, str]] = None,
    ) -> None:
        self.config = config
        self.registry = registry
        # Lazy: system_context (list_collections, get_collection_info, etc.) loaded on first use.
        self._system_context: Optional[SystemContext] = system_context
        self.agent_descriptions = dict(self.DEFAULT_AGENT_DESCRIPTIONS)
        if agent_descriptions:
            self.agent_descriptions.update(agent_descriptions)
        self._prompt = SupervisorPrompt()
        # Lazy: sub-agents are built on first use, not up front.
        self._agents: Dict[str, SubAgentGraph] = dict(agents) if agents else {}
        self._agent_names = list(self.agent_descriptions.keys())
        if self._system_context is not None:
            self._system_context.agent_names = self._agent_names
        logger.info("Supervisor initialized (context and sub-agents on first use): %s", self._agent_names)

    def _ensure_system_context(self) -> SystemContext:
        """Load system context (list_collections, get_collection_info, etc.) on first use."""
        if self._system_context is None:
            logger.debug("Loading system context (list_collections, get_collection_info) on first use")
            self._system_context = load_system_context(self.registry)
            self._system_context.agent_names = self._agent_names
        return self._system_context

    @property
    def system_context(self) -> SystemContext:
        return self._ensure_system_context()

    def _get_agent(self, name: str) -> Optional[SubAgentGraph]:
        """Get sub-agent by name; build and cache on first use."""
        if name in self._agents:
            return self._agents[name]
        if name not in self._agent_names:
            return None
        from artemis.agent.agents import (
            build_collection_agent,
            build_ingestion_agent,
            build_rag_agent,
        )
        builders = {
            "rag_search": build_rag_agent,
            "ingestion": build_ingestion_agent,
            "collection_management": build_collection_agent,
        }
        builder = builders.get(name)
        if not builder:
            return None
        self._agents[name] = builder(
            self.config, self.registry, self.system_context
        )
        logger.info("Built sub-agent on first use: %s", name)
        return self._agents[name]

    def _get_llm_client(self) -> Any:
        if self.config.provider == "groq":
            return GroqClient(
                api_key=self.config.groq_api_key,
                model_name=self.config.model_name,
            )
        return OpenAIClient(
            api_key=self.config.openai_api_key,
            model_name=self.config.model_name,
        )

    # Short acknowledgments/affirmations that never need a sub-agent; route to direct without calling LLM.
    DIRECT_ACK_PHRASES = frozenset({
        "that's great", "sounds good", "ok", "okay", "perfect", "got it", "thanks", "thank you",
        "cool", "good", "understood", "noted", "great", "awesome", "nice", "alright", "sure",
        "hi", "hello", "hey", "yes", "no", "yep", "nope", "good to know", "makes sense",
        "that's good", "sounds good to me", "looks good", "all good", "fine", "done",
    })

    def _route(self, query: str, last_routed_to: Optional[str] = None) -> str:
        q = (query or "").strip().lower()
        if q in self.DIRECT_ACK_PHRASES:
            logger.debug("Supervisor: acknowledgment phrase -> direct (no LLM)")
            return "direct"
        # Short phrase that looks like an ack (e.g. "that's great, sounds good"): no question/action words, has ack word
        if len(q) <= 80 and any(
            ack in q for ack in ("great", "sounds good", "thanks", "perfect", "cool", "got it", "nice", "awesome", "understood", "noted")
        ) and not any(
            w in q for w in ("?", "search", "ingest", "create", "list", "what", "how", "why", "where", "when", "which", "show", "find", "add", "delete", "check", "tell")
        ):
            logger.debug("Supervisor: short acknowledgment-like query -> direct (no LLM)")
            return "direct"
        context: Dict[str, Any] = {
            "agents": [
                {"name": k, "description": v}
                for k, v in self.agent_descriptions.items()
            ],
            "collections": self.system_context.collections,
            "last_routed_to": last_routed_to,
        }
        system_prompt = self._prompt.render_system(context)
        user_prompt = self._prompt.render_user(query)
        try:
            response = self._get_llm_client().generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=150,
            )
        except Exception as e:
            logger.warning("Supervisor LLM call failed: %s; defaulting to direct", e)
            return "direct"

        parsed: Optional[Dict[str, Any]] = None
        try:
            parsed = json.loads(response.strip())
        except json.JSONDecodeError:
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL
            )
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        if not parsed or not isinstance(parsed, dict):
            logger.warning("Supervisor could not parse routing JSON; defaulting to direct")
            return "direct"
        agent = parsed.get("agent")
        if not isinstance(agent, str):
            logger.warning("Supervisor response missing or invalid 'agent' field; defaulting to direct")
            return "direct"
        agent = agent.strip()
        if agent == "direct" or agent in self._agent_names:
            return agent
        logger.warning("Supervisor returned unknown agent %r; defaulting to direct", agent)
        return "direct"

    def _direct_answer(self, query: str, message_history: Optional[list] = None) -> AgentState:
        # Only inject tool list when the user is asking about tools/capabilities; otherwise keep replies short (e.g. "hi" -> brief greeting).
        q = (query or "").strip().lower()
        tool_related = any(
            phrase in q
            for phrase in (
                "tool", "tools", "capabilities", "what can you", "what do you have",
                "what are your", "how do you work", "what can the system", "available",
                "list of ", "what options", "what are the ",
            )
        )
        tool_calls_summary = None
        if tool_related:
            tool_list = self.registry.list_tools()
            lines = ["Available tools (name + description):"]
            for t in tool_list:
                name = t.get("name", "?")
                desc = (t.get("description") or "").strip()
                lines.append(f"- {name}: {desc}")
            tool_calls_summary = "\n".join(lines) if lines else None

        state: AgentState = {
            "query": query,
            "message_history": message_history,
            "tool_calls": [],
            "tool_calls_summary": tool_calls_summary,
            "intent": "direct",
            "step_count": 0,
            "final_answer": None,
            "error": None,
            "retrieved_docs": [],
            "tool_name": None,
            "tool_args": None,
            "confidence": 1.0,
            "reasoning": "Direct answer — no tools needed.",
        }
        return direct_answer_node(state, self.config)

    def invoke(
        self,
        query: str,
        message_history: Optional[list] = None,
        last_routed_to: Optional[str] = None,
    ) -> AgentState:
        agent_name = self._route(query, last_routed_to=last_routed_to)
        logger.info("Supervisor routing to: %s", agent_name)
        if agent_name == "direct":
            result = self._direct_answer(query, message_history=message_history)
        else:
            sub = self._get_agent(agent_name)
            if sub is None:
                result = self._direct_answer(query, message_history=message_history)
            else:
                try:
                    result = sub.invoke(query, message_history=message_history)
                except Exception:
                    logger.exception("Sub-agent %s failed; falling back to direct answer", agent_name)
                    result = self._direct_answer(query, message_history=message_history)
        return {**result, "routed_to": agent_name}

    async def ainvoke(
        self,
        query: str,
        message_history: Optional[list] = None,
        last_routed_to: Optional[str] = None,
    ) -> AgentState:
        agent_name = self._route(query, last_routed_to=last_routed_to)
        logger.info("Supervisor routing to: %s", agent_name)
        if agent_name == "direct":
            result = self._direct_answer(query, message_history=message_history)
        else:
            sub = self._get_agent(agent_name)
            if sub is None:
                result = self._direct_answer(query, message_history=message_history)
            else:
                try:
                    result = await sub.ainvoke(query, message_history=message_history)
                except Exception:
                    logger.exception("Sub-agent %s failed; falling back to direct answer", agent_name)
                    result = self._direct_answer(query, message_history=message_history)
        return {**result, "routed_to": agent_name}

    def register_agent(
        self,
        name: str,
        agent: SubAgentGraph,
        description: str,
    ) -> None:
        self._agents[name] = agent
        self.agent_descriptions[name] = description
        if name not in self._agent_names:
            self._agent_names.append(name)
        self.system_context.agent_names = list(self._agent_names)
        logger.info("Registered new agent: %s", name)


__all__ = ["Supervisor"]
