"""
Tests for the agent graph flow: planner -> tool_node -> planner -> direct_answer.
Uses mocked LLM and a stub registry (no real RAG or API keys).
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from artemis.agent.config import AgentConfig
from artemis.agent.graph import AgentGraph
from artemis.agent.tools import ToolRegistry


def _echo_tool(**kwargs):
    """Stub tool that returns {echo: query} for assertions."""
    return {"echo": kwargs.get("query", "")}


@pytest.fixture
def stub_registry():
    """Registry with a single 'echo' tool."""
    r = ToolRegistry()
    r.register(
        "echo",
        _echo_tool,
        "Echo the query",
        {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    )
    return r


@pytest.fixture
def config_no_env():
    """Config with test API key so tests don't depend on env."""
    return AgentConfig(
        provider="groq",
        groq_api_key="test-key",
        max_tool_steps=5,
    )


def test_agent_flow_planner_tool_then_direct(config_no_env, stub_registry):
    """
    Mock LLM: 1st call planner -> tool echo, 2nd call planner -> direct, 3rd call direct_answer.
    Assert: final_answer set, tool_calls has one entry (echo, ok True), intent is direct.
    """
    planner_responses = [
        json.dumps({
            "intent": "tool",
            "tool_name": "echo",
            "tool_args": {"query": "hi"},
            "confidence": 0.9,
            "reasoning": "test",
        }),
        json.dumps({
            "intent": "direct",
            "confidence": 0.9,
            "reasoning": "done",
        }),
    ]
    direct_answer_response = "Echo says: hi"
    call_count = [0]

    def mock_generate(system_prompt=None, user_prompt=None, temperature=None, max_tokens=None):
        call_count[0] += 1
        # First and second calls are planner; third is direct_answer
        if call_count[0] == 1:
            return planner_responses[0]
        if call_count[0] == 2:
            return planner_responses[1]
        return direct_answer_response

    with patch("artemis.agent.nodes.planner.GroqClient") as MockGroq:
        with patch("artemis.agent.nodes.direct_answer.GroqClient") as MockGroqDA:
            mock_instance = MagicMock()
            mock_instance.generate = mock_generate
            MockGroq.return_value = mock_instance
            MockGroqDA.return_value = mock_instance

            graph = AgentGraph(
                config=config_no_env,
                registry=stub_registry,
                max_tool_steps=5,
            )
            result = graph.invoke("hi")

    assert result.get("final_answer") == direct_answer_response
    assert result.get("intent") == "direct"
    tool_calls = result.get("tool_calls", [])
    assert len(tool_calls) == 1
    assert tool_calls[0]["tool_name"] == "echo"
    assert tool_calls[0]["arguments"] == {"query": "hi"}
    assert tool_calls[0]["result"] == {"echo": "hi"}
    assert tool_calls[0]["ok"] is True
