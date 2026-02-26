"""
Supervisor: routes user queries to the correct sub-agent via a single LLM call.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, Dict, Optional

from artemis.agent.config import AgentConfig
from artemis.agent.context import SystemContext
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
        "ingestion": "Add data to the knowledge base (ingest documents, URLs, etc.).",
        "collection_management": "Manage Qdrant collections (create, delete, list).",
    }

    def __init__(
        self,
        config: AgentConfig,
        registry: ToolRegistry,
        system_context: SystemContext,
        agents: Optional[Dict[str, SubAgentGraph]] = None,
        agent_descriptions: Optional[Dict[str, str]] = None,
    ) -> None:
        self.config = config
        self.registry = registry
        self.system_context = system_context
        self.agent_descriptions = dict(self.DEFAULT_AGENT_DESCRIPTIONS)
        if agent_descriptions:
            self.agent_descriptions.update(agent_descriptions)
        self.agents: Dict[str, SubAgentGraph] = (
            agents if agents is not None else self._build_default_agents()
        )
        self.system_context.agent_names = list(self.agents.keys())
        self._prompt = SupervisorPrompt()
        logger.info("Supervisor initialized with agents: %s", list(self.agents.keys()))

    def _build_default_agents(self) -> Dict[str, SubAgentGraph]:
        from artemis.agent.agents import (
            build_collection_agent,
            build_ingestion_agent,
            build_rag_agent,
        )

        return {
            "rag_search": build_rag_agent(
                self.config, self.registry, self.system_context
            ),
            "ingestion": build_ingestion_agent(
                self.config, self.registry, self.system_context
            ),
            "collection_management": build_collection_agent(
                self.config, self.registry, self.system_context
            ),
        }

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

    def _route(self, query: str) -> str:
        context: Dict[str, Any] = {
            "agents": [
                {"name": k, "description": v}
                for k, v in self.agent_descriptions.items()
            ],
            "collections": self.system_context.collections,
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
        if agent in self.agents or agent == "direct":
            return agent
        logger.warning("Supervisor returned unknown agent %r; defaulting to direct", agent)
        return "direct"

    def _direct_answer(self, query: str) -> AgentState:
        state: AgentState = {
            "query": query,
            "tool_calls": [],
            "tool_calls_summary": None,
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

    def invoke(self, query: str) -> AgentState:
        agent_name = self._route(query)
        logger.info("Supervisor routing to: %s", agent_name)
        if agent_name == "direct" or agent_name not in self.agents:
            result = self._direct_answer(query)
        else:
            try:
                result = self.agents[agent_name].invoke(query)
            except Exception:
                logger.exception("Sub-agent %s failed; falling back to direct answer", agent_name)
                result = self._direct_answer(query)
        return {**result, "routed_to": agent_name}

    async def ainvoke(self, query: str) -> AgentState:
        agent_name = self._route(query)
        logger.info("Supervisor routing to: %s", agent_name)
        if agent_name == "direct" or agent_name not in self.agents:
            result = self._direct_answer(query)
        else:
            try:
                result = await self.agents[agent_name].ainvoke(query)
            except Exception:
                logger.exception("Sub-agent %s failed; falling back to direct answer", agent_name)
                result = self._direct_answer(query)
        return {**result, "routed_to": agent_name}

    def register_agent(
        self,
        name: str,
        agent: SubAgentGraph,
        description: str,
    ) -> None:
        self.agents[name] = agent
        self.agent_descriptions[name] = description
        self.system_context.agent_names = list(self.agents.keys())
        logger.info("Registered new agent: %s", name)


__all__ = ["Supervisor"]
