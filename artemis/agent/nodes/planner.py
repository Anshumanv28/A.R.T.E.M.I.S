"""
Planner node for intent classification and routing.

Determines whether to use a tool (e.g. RAG search, ingest) or answer directly.
Outputs intent, and when tool: tool_name and tool_args. Validates against
a strict JSON schema; on failure falls back to intent="direct".
"""

import json
import re
from typing import Any, Dict, List, Optional

from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.tools.registry import ToolRegistry
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.utils import get_logger

logger = get_logger(__name__)

# Strict schema for planner output: intent required; tool_name and tool_args when intent is "tool"
PLANNER_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["intent"],
    "properties": {
        "intent": {"type": "string", "enum": ["tool", "direct"]},
        "tool_name": {"type": "string"},
        "tool_args": {"type": "object"},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "additionalProperties": True,
}


def _validate_planner_response(data: Dict[str, Any], registry: ToolRegistry) -> Dict[str, Any]:
    """
    Validate and normalize planner response. Ensures intent in ["tool","direct"];
    when intent=="tool", requires tool_name in registry and tool_args (dict).
    Returns normalized dict with intent, tool_name (or None), tool_args (or None), confidence, reasoning.
    """
    intent = (data.get("intent") or "direct").lower().strip()
    if intent not in ("tool", "direct"):
        intent = "direct"
    tool_name = data.get("tool_name")
    if isinstance(tool_name, str):
        tool_name = tool_name.strip() or None
    else:
        tool_name = None
    tool_args = data.get("tool_args")
    if not isinstance(tool_args, dict):
        tool_args = {}
    if intent == "tool" and tool_name and tool_name not in [t["name"] for t in registry.list_tools()]:
        logger.warning(f"Planner chose unknown tool '{tool_name}'; falling back to direct")
        intent = "direct"
        tool_name = None
        tool_args = {}
    if intent == "tool" and not tool_name:
        intent = "direct"
        tool_args = {}
    confidence = data.get("confidence")
    if confidence is not None:
        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.5
    else:
        confidence = 0.5
    reasoning = data.get("reasoning")
    if reasoning is not None and not isinstance(reasoning, str):
        reasoning = str(reasoning)
    else:
        reasoning = reasoning or ""
    return {
        "intent": intent,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _parse_planner_json(response: str, registry: ToolRegistry) -> Optional[Dict[str, Any]]:
    """Extract JSON object from LLM response and validate. Returns None on failure."""
    # Try to find a JSON object in the response
    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            return _validate_planner_response(parsed, registry)
        except json.JSONDecodeError:
            pass
    try:
        parsed = json.loads(response.strip())
        return _validate_planner_response(parsed, registry)
    except json.JSONDecodeError:
        return None


def _normalize_path(p: str) -> str:
    """Normalize a path for comparison (strip, forward slashes, lower on Windows)."""
    if not p or not isinstance(p, str):
        return ""
    p = p.strip().replace("\\", "/").rstrip("/")
    return p.lower() if p else p


def _format_tools_for_prompt(tools: List[Dict[str, Any]]) -> str:
    """Format registry.list_tools() for the planner prompt."""
    lines = []
    for t in tools:
        name = t.get("name", "?")
        desc = t.get("description", "")
        schema = t.get("parameters_schema")
        if schema and schema.get("properties"):
            params = ", ".join(schema.get("properties", {}).keys())
            lines.append(f"- {name}: {desc} (parameters: {params})")
        else:
            lines.append(f"- {name}: {desc}")
    return "\n".join(lines) if lines else "(No tools registered)"


def planner_node(
    state: AgentState,
    config: AgentConfig,
    registry: ToolRegistry,
    max_tool_steps: int = 10,
) -> AgentState:
    """
    Classify intent (tool vs direct) and set tool_name/tool_args when tool.

    Uses LLM with available tools from registry. Enforces step limit: if
    step_count >= max_tool_steps, forces intent="direct". Validates LLM
    output with strict contract; on parse failure falls back to intent="direct".
    """
    query = state.get("query", "")
    step_count = state.get("step_count", 0)
    tool_calls = state.get("tool_calls") or []

    if not query:
        logger.warning("Empty query in planner node")
        return {
            **state,
            "intent": "direct",
            "confidence": 0.0,
            "tool_name": None,
            "tool_args": None,
            "error": "Empty query",
        }

    # Step limit: force direct when at or over max tool steps
    if step_count >= max_tool_steps:
        logger.info(f"Step limit reached ({step_count} >= {max_tool_steps}); forcing intent=direct")
        return {
            **state,
            "intent": "direct",
            "confidence": 1.0,
            "tool_name": None,
            "tool_args": None,
            "reasoning": "Step limit reached; answering with available context.",
        }

    tools_list = registry.list_tools()
    tools_blob = _format_tools_for_prompt(tools_list)

    system_prompt = f"""You are an intent classifier for an agent that can use tools or answer directly.

Available tools:
{tools_blob}

Your task: decide whether to call ONE tool (intent="tool") or to answer the user directly (intent="direct").

Use intent="tool" when:
- The user needs to search the knowledge base (use search_documents with query).
- The user wants to ingest a file, list collections, get collection info, create/clear/delete collections.
- You need information from a tool before you can answer.

Use intent="direct" when:
- You can answer from general knowledge or from prior tool results already in the conversation.
- The user query is conversational or doesn't require any tool.
- You have already gathered enough information from previous tool calls.
- You have already run ingest_directory successfully for a directory (do not call ingest_directory again for the same directory).
- You have already run search_documents and got results (use intent=direct to answer; do not call search_documents again).

Call ingest_directory at most once per directory per user request. After search_documents has returned results, use intent=direct to answer; do not call search_documents again. After a successful ingest_directory (ingested_count > 0), use intent="direct" to confirm or answer; do not call ingest_directory again for the same path.

You have at most {max_tool_steps} tool calls total; when in doubt, move to direct.

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{"intent": "tool" or "direct", "tool_name": "<name>" (only if intent is tool), "tool_args": {{}} (only if intent is tool, with the right parameters), "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

For search_documents use tool_args like {{"query": "user query here", "k": 5}}.
For ingest_file use {{"path": "/path/to/file", "file_type": "pdf"}} (file_type: csv, pdf, docx, md, text).
For ingest_directory use {{"directory_path": "RAG_demo/techcorp_docs", "file_extension": "md"}} to ingest all .md files in a folder.
For list_collections use {{}}.
For get_collection_info use {{"collection_name": "name"}}.
For create_collection use {{"collection_name": "name"}} or {{"collection_name": "name", "embedding_dim": 384}}.
For clear_collection/delete_collection use {{"collection_name": "name", "confirm": true}} (only after user confirmed).

Default collection: The RAG knowledge base uses the collection named "artemis_documents". When the user asks to delete, clear, or get info about "the collection" or "the RAG collection" without giving a name, use collection_name "artemis_documents" (not "RAG").
"""

    # Include prior tool results so planner can decide to go direct after tools
    prior_context = ""
    if tool_calls:
        prior_context = "\nPrior tool results (you may now answer using this context):\n"
        for i, tc in enumerate(tool_calls, 1):
            ok = tc.get("ok", True)
            status = "ok" if ok else "error"
            name = tc.get("tool_name", "?")
            line = f"  {i}. {name}: {status}"
            result = tc.get("result")
            if ok and isinstance(result, dict) and name == "ingest_directory":
                ingested = result.get("ingested_count")
                if ingested is not None:
                    line += f", ingested_count={ingested}"
            prior_context += line + "\n"
    user_prompt = f"Query: {query}{prior_context}\n\nClassify intent and respond with JSON only."

    if config.provider == "groq":
        llm_client = GroqClient(
            api_key=config.groq_api_key,
            model_name=config.model_name,
        )
    else:
        llm_client = OpenAIClient(
            api_key=config.openai_api_key,
            model_name=config.model_name,
        )

    try:
        response = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=400,
        )
        validated = _parse_planner_json(response, registry)
        if validated is None:
            logger.warning("Planner JSON parse failed; falling back to intent=direct")
            return {
                **state,
                "intent": "direct",
                "confidence": 0.5,
                "tool_name": None,
                "tool_args": None,
                "reasoning": "Parse error; answering directly.",
            }
        # Block repeated search_documents (one search is enough; avoids token overflow in direct_answer)
        if validated.get("intent") == "tool" and validated.get("tool_name") == "search_documents":
            for tc in tool_calls:
                if tc.get("tool_name") == "search_documents" and tc.get("ok") and tc.get("result"):
                    logger.info(
                        "Blocking repeated search_documents; forcing intent=direct"
                    )
                    validated = {
                        **validated,
                        "intent": "direct",
                        "tool_name": None,
                        "tool_args": None,
                        "reasoning": "Search already returned results; answering with available context.",
                    }
                    break
        # Block duplicate ingest_directory for the same directory in this run
        if validated.get("intent") == "tool" and validated.get("tool_name") == "ingest_directory":
            new_args = validated.get("tool_args") or {}
            new_path = _normalize_path(new_args.get("directory_path") or "")
            for tc in tool_calls:
                if tc.get("tool_name") != "ingest_directory" or not tc.get("ok"):
                    continue
                prev_args = tc.get("arguments") or {}
                prev_path = _normalize_path(prev_args.get("directory_path") or "")
                if prev_path and new_path and prev_path == new_path:
                    logger.info(
                        "Blocking duplicate ingest_directory for same path; forcing intent=direct"
                    )
                    validated = {
                        **validated,
                        "intent": "direct",
                        "tool_name": None,
                        "tool_args": None,
                        "reasoning": "Ingest already completed for this directory; answering with available context.",
                    }
                    break
        logger.info(
            f"Intent: {validated['intent']}, confidence: {validated['confidence']:.2f}, reasoning: {validated['reasoning'][:80]}"
        )
        return {
            **state,
            "intent": validated["intent"],
            "confidence": validated["confidence"],
            "reasoning": validated["reasoning"],
            "tool_name": validated.get("tool_name"),
            "tool_args": validated.get("tool_args"),
        }
    except Exception as e:
        logger.exception(f"Error in planner node: {e}")
        return {
            **state,
            "intent": "direct",
            "confidence": 0.5,
            "tool_name": None,
            "tool_args": None,
            "error": f"Planner error: {str(e)}",
        }
