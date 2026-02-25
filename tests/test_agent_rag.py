"""
Tests for agent + RAG tool: planner chooses search_documents, tool runs, direct_answer sees results.
Uses mock retriever and mocked LLM; no Qdrant or API keys required.
"""

import json
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

import pytest

from artemis.agent.config import AgentConfig
from artemis.agent.graph import AgentGraph
from artemis.agent.tools import build_rag_registry


RAG_DOCS = [
    {"text": "Artemis is a retrieval system.", "score": 0.95, "metadata": {}},
]


class _MockRetriever:
    """Minimal retriever for tests; records retrieve calls and returns fixed docs."""

    def __init__(self, docs: List[Dict[str, Any]] = None):
        self.docs = docs or RAG_DOCS
        self.retrieve_calls = []

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        self.retrieve_calls.append((query, k))
        return self.docs[:k]


@pytest.fixture
def mock_retriever_with_docs():
    """Retriever that returns fixed RAG_DOCS and records retrieve calls."""
    return _MockRetriever(docs=RAG_DOCS)


@pytest.fixture
def config_no_env():
    """Config with test API key."""
    return AgentConfig(
        provider="groq",
        groq_api_key="test-key",
        max_tool_steps=5,
    )


def test_agent_rag_search_tool_invoked_and_result_in_tool_calls(config_no_env, mock_retriever_with_docs):
    """
    Mock LLM: planner 1 -> tool search_documents, planner 2 -> direct, then direct_answer.
    Assert: tool_calls has one entry (search_documents, ok True, result = RAG doc list);
    final_answer non-empty; mock retriever.retrieve was called with expected query.
    """
    planner_responses = [
        json.dumps({
            "intent": "tool",
            "tool_name": "search_documents",
            "tool_args": {"query": "What is Artemis?"},
            "confidence": 0.9,
            "reasoning": "need to search",
        }),
        json.dumps({
            "intent": "direct",
            "confidence": 0.9,
            "reasoning": "have context",
        }),
    ]
    direct_answer_response = "Based on the documents, Artemis is a retrieval system."
    call_count = [0]

    def mock_generate(system_prompt=None, user_prompt=None, temperature=None, max_tokens=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return planner_responses[0]
        if call_count[0] == 2:
            return planner_responses[1]
        return direct_answer_response

    registry = build_rag_registry(mock_retriever_with_docs, indexer=None, default_k=5)

    with patch("artemis.agent.nodes.planner.GroqClient") as MockGroq:
        with patch("artemis.agent.nodes.direct_answer.GroqClient") as MockGroqDA:
            mock_instance = MagicMock()
            mock_instance.generate = mock_generate
            MockGroq.return_value = mock_instance
            MockGroqDA.return_value = mock_instance

            graph = AgentGraph(config=config_no_env, registry=registry, max_tool_steps=5)
            result = graph.invoke("What is Artemis?")

    assert result.get("final_answer") == direct_answer_response
    tool_calls = result.get("tool_calls", [])
    assert len(tool_calls) == 1
    assert tool_calls[0]["tool_name"] == "search_documents"
    assert tool_calls[0]["ok"] is True
    assert tool_calls[0]["result"] == RAG_DOCS
    assert mock_retriever_with_docs.retrieve_calls == [("What is Artemis?", 5)]
