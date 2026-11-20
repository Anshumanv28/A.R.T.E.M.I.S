"""
Unit tests for live per-request observability: per-tool-call timing in
tool_node, and routing/agent latency breakdown on Supervisor.invoke().

Uses mocked LLM and a stub registry (no real RAG, Qdrant, or API keys) --
same pattern as test_agent_flow.py.
"""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from artemis.agent.config import AgentConfig
from artemis.agent.nodes.tool_node import tool_node
from artemis.agent.supervisor import Supervisor
from artemis.agent.tools import ToolRegistry


def _slow_echo_tool(**kwargs):
    time.sleep(0.01)
    return {"echo": kwargs.get("query", "")}


@pytest.fixture
def stub_registry():
    r = ToolRegistry()
    r.register(
        "echo",
        _slow_echo_tool,
        "Echo the query",
        {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    )
    r.register(
        "list_things",
        lambda **kwargs: ["a", "b", "c"],
        "Return a list",
        {"type": "object", "properties": {}},
    )
    return r


@pytest.fixture
def config_no_env():
    return AgentConfig(provider="groq", groq_api_key="test-key", max_tool_steps=5)


def test_tool_node_records_duration_and_result_count(stub_registry):
    state = {
        "tool_name": "echo",
        "tool_args": {"query": "hi"},
        "tool_calls": [],
        "step_count": 0,
    }
    result = tool_node(state, stub_registry)
    call = result["tool_calls"][0]
    assert call["ok"] is True
    assert call["duration_ms"] >= 10  # tool slept 10ms
    assert call["result_count"] is None  # result is a dict, not a list


def test_tool_node_records_result_count_for_list_result(stub_registry):
    state = {
        "tool_name": "list_things",
        "tool_args": {},
        "tool_calls": [],
        "step_count": 0,
    }
    result = tool_node(state, stub_registry)
    call = result["tool_calls"][0]
    assert call["result_count"] == 3
    assert call["duration_ms"] >= 0


def test_tool_node_missing_tool_still_has_duration_shape(stub_registry):
    state = {
        "tool_name": "does_not_exist",
        "tool_args": {},
        "tool_calls": [],
        "step_count": 0,
    }
    result = tool_node(state, stub_registry)
    call = result["tool_calls"][0]
    assert call["ok"] is False
    assert "duration_ms" in call
    assert "result_count" in call


def test_supervisor_invoke_direct_has_latency_breakdown(config_no_env):
    registry = ToolRegistry()
    with patch("artemis.agent.supervisor.GroqClient") as MockGroq, \
         patch("artemis.agent.nodes.direct_answer.GroqClient") as MockGroqDA:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = "Hi there!"
        MockGroq.return_value = mock_instance
        MockGroqDA.return_value = mock_instance

        supervisor = Supervisor(config=config_no_env, registry=registry)
        result = supervisor.invoke("Thanks")

    assert result["routed_to"] == "direct"
    assert result["routing_latency_ms"] >= 0
    assert result["agent_latency_ms"] >= 0


def test_supervisor_invoke_sub_agent_has_latency_breakdown(config_no_env, stub_registry):
    with patch("artemis.agent.supervisor.GroqClient") as MockGroq, \
         patch("artemis.agent.nodes.planner.GroqClient") as MockGroqPlanner, \
         patch("artemis.agent.nodes.direct_answer.GroqClient") as MockGroqDA:

        route_mock = MagicMock()
        route_mock.generate.return_value = json.dumps({"agent": "rag_search"})
        MockGroq.return_value = route_mock

        planner_mock = MagicMock()
        planner_mock.generate.return_value = json.dumps({
            "intent": "direct", "confidence": 0.9, "reasoning": "done",
        })
        MockGroqPlanner.return_value = planner_mock

        answer_mock = MagicMock()
        answer_mock.generate.return_value = "Here is your answer."
        MockGroqDA.return_value = answer_mock

        supervisor = Supervisor(
            config=config_no_env,
            registry=stub_registry,
            agents={},
            agent_descriptions={"rag_search": "Search the knowledge base."},
        )
        # Avoid building the real rag_search SubAgentGraph (needs full prompt/context
        # wiring); patch _get_agent to return a minimal stub with an invoke() method.
        stub_agent = MagicMock()
        stub_agent.invoke.return_value = {
            "final_answer": "Here is your answer.",
            "tool_calls": [],
            "error": None,
        }
        with patch.object(Supervisor, "_get_agent", return_value=stub_agent):
            result = supervisor.invoke("What's in the knowledge base?")

    assert result["routed_to"] == "rag_search"
    assert result["routing_latency_ms"] >= 0
    assert result["agent_latency_ms"] >= 0
