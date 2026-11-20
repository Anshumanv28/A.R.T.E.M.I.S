"""
Tests for LLM-based entity/relationship extraction (artemis/graph/extraction.py).
No real LLM call -- the client's .generate() is a stub returning canned JSON.
"""

import json

from artemis.graph.extraction import extract_entities_and_relationships


class _StubLLMClient:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def generate(self, system_prompt, user_prompt, **kwargs):
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt, **kwargs})
        return self.response


def test_extracts_entities_and_relationships_from_clean_json():
    response = json.dumps(
        {
            "entities": [
                {"name": "Project Apollo", "type": "Project"},
                {"name": "Team Alpha", "type": "Organization"},
            ],
            "relationships": [{"source": "Team Alpha", "relation": "manages", "target": "Project Apollo"}],
        }
    )
    client = _StubLLMClient(response)
    result = extract_entities_and_relationships("some document text", client)

    assert result["entities"] == [
        {"name": "Project Apollo", "type": "Project"},
        {"name": "Team Alpha", "type": "Organization"},
    ]
    assert result["relationships"] == [{"source": "Team Alpha", "relation": "manages", "target": "Project Apollo"}]


def test_extracts_json_embedded_in_markdown_or_extra_text():
    response = "Here you go:\n```json\n" + json.dumps(
        {"entities": [{"name": "X", "type": "Other"}], "relationships": []}
    ) + "\n```"
    client = _StubLLMClient(response)
    result = extract_entities_and_relationships("text", client)
    assert result["entities"] == [{"name": "X", "type": "Other"}]


def test_drops_relationships_whose_source_or_target_is_not_a_listed_entity():
    """The LLM sometimes references an entity it forgot to list -- those relationships must be dropped, not crash."""
    response = json.dumps(
        {
            "entities": [{"name": "A", "type": "Other"}],
            "relationships": [
                {"source": "A", "relation": "uses", "target": "B"},  # B was never listed
                {"source": "C", "relation": "uses", "target": "A"},  # C was never listed
            ],
        }
    )
    client = _StubLLMClient(response)
    result = extract_entities_and_relationships("text", client)
    assert result["relationships"] == []


def test_defaults_missing_entity_type_to_other():
    response = json.dumps({"entities": [{"name": "X"}], "relationships": []})
    client = _StubLLMClient(response)
    result = extract_entities_and_relationships("text", client)
    assert result["entities"] == [{"name": "X", "type": "Other"}]


def test_malformed_response_returns_empty_graph_not_an_exception():
    client = _StubLLMClient("not json at all, sorry")
    result = extract_entities_and_relationships("text", client)
    assert result == {"entities": [], "relationships": []}


def test_llm_exception_returns_empty_graph_not_an_exception():
    class _FailingClient:
        def generate(self, **kwargs):
            raise RuntimeError("LLM is down")

    result = extract_entities_and_relationships("text", _FailingClient())
    assert result == {"entities": [], "relationships": []}


def test_truncates_very_long_text_before_sending_to_llm():
    from artemis.graph.extraction import MAX_EXTRACTION_CHARS

    client = _StubLLMClient(json.dumps({"entities": [], "relationships": []}))
    long_text = "x" * (MAX_EXTRACTION_CHARS + 5000)
    extract_entities_and_relationships(long_text, client)
    assert len(client.calls[0]["user_prompt"]) == MAX_EXTRACTION_CHARS
