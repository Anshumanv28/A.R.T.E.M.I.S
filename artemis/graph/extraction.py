"""
LLM-based entity/relationship extraction for GraphRAG.

Deliberately open-vocabulary (entity type and relation are free strings the
LLM infers, not a fixed enum) rather than a formal NER+relation-extraction
model -- simpler to wire into the existing LLM clients (GroqClient/
OpenAIClient already used for agentic chunking), at the cost of being less
consistent than a dedicated model. Good enough to prove the GraphRAG
mechanism works; a stricter schema/dedicated extractor is future work if
extraction quality turns out to be the bottleneck.
"""

import json
import re
from typing import Any, Dict, List

from artemis.utils import get_logger

logger = get_logger(__name__)

MAX_EXTRACTION_CHARS = 6000  # keep the extraction prompt (and cost) bounded for long documents

_SYSTEM_PROMPT = """You extract entities and relationships from text for a knowledge graph.

Return ONLY a JSON object, no markdown, no extra text, in this exact shape:
{"entities": [{"name": "<string>", "type": "<Person|Organization|Project|Technology|Concept|Event|Other>"}],
 "relationships": [{"source": "<entity name>", "relation": "<short verb phrase, e.g. manages, uses, reports_to>", "target": "<entity name>"}]}

Rules:
- Only extract entities/relationships explicitly stated in the text, never inferred or guessed.
- Use the exact same "name" string for an entity every time it's referenced, so relationships link correctly.
- source and target in relationships must each match a "name" in entities.
- If nothing worth extracting is found, return {"entities": [], "relationships": []}.
"""


def _parse_extraction_response(response: str) -> Dict[str, List[Dict[str, Any]]]:
    try:
        parsed = json.loads(response.strip())
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response, re.DOTALL)
        parsed = None
        if match:
            try:
                parsed = json.loads(match.group())
            except json.JSONDecodeError:
                pass
    if not isinstance(parsed, dict):
        logger.warning("Could not parse graph extraction response as JSON; returning empty graph")
        return {"entities": [], "relationships": []}

    entities = [
        {"name": str(e.get("name", "")).strip(), "type": str(e.get("type", "Other")).strip() or "Other"}
        for e in parsed.get("entities", [])
        if isinstance(e, dict) and str(e.get("name", "")).strip()
    ]
    known_names = {e["name"] for e in entities}
    relationships = [
        {
            "source": str(r.get("source", "")).strip(),
            "relation": str(r.get("relation", "")).strip() or "related_to",
            "target": str(r.get("target", "")).strip(),
        }
        for r in parsed.get("relationships", [])
        if isinstance(r, dict)
        and str(r.get("source", "")).strip() in known_names
        and str(r.get("target", "")).strip() in known_names
    ]
    return {"entities": entities, "relationships": relationships}


def extract_entities_and_relationships(text: str, llm_client: Any) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract {"entities": [{name, type}], "relationships": [{source, relation, target}]}
    from text using the given LLM client (must expose .generate(system_prompt, user_prompt, ...)).

    Relationships whose source/target don't match an extracted entity name are
    dropped (the LLM occasionally references an entity it forgot to list).
    """
    truncated = text[:MAX_EXTRACTION_CHARS]
    try:
        response = llm_client.generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=truncated,
            temperature=0.0,
            max_tokens=2048,
        )
    except Exception as e:
        logger.warning(f"Graph extraction LLM call failed: {e}")
        return {"entities": [], "relationships": []}
    return _parse_extraction_response(response)


__all__ = ["extract_entities_and_relationships"]
