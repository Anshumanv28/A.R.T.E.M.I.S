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
from artemis.agent.prompts import load_planner_prompt
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.utils import get_logger

logger = get_logger(__name__)

# Max conversation turns to include in context (2 exchanges = 4 messages)
_MAX_MESSAGE_HISTORY = 4
_MAX_ASSISTANT_CHARS = 400


def _format_message_history(history: Optional[List[Dict[str, Any]]]) -> str:
    """Format message_history for prompt context. Uses last N messages, truncates long assistant replies."""
    if not history:
        return ""
    take = history[-_MAX_MESSAGE_HISTORY:]
    lines = []
    for m in take:
        role = (m.get("role") or "user").lower()
        content = (m.get("content") or "").strip()
        if role == "assistant" and len(content) > _MAX_ASSISTANT_CHARS:
            content = content[:_MAX_ASSISTANT_CHARS].rstrip() + "..."
        lines.append(f"{role.capitalize()}: {content}")
    return "Recent conversation:\n" + "\n".join(lines) + "\n\n"


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


def _rag_options_blob(tools_list: List[Dict[str, Any]]) -> str:
    """Build a short RAG options reference from registries and tool schema (2-4 lines)."""
    try:
        from artemis.rag.ingestion.chunkers.registry import CHUNKERS
        from artemis.rag.ingestion.converters.csv_converter import CSV_CONVERTERS, DocumentSchema
        chunk_vals = [s.value for s in CHUNKERS.keys()]
        schema_vals = [s.value for s in CSV_CONVERTERS.keys()] if CSV_CONVERTERS else [s.value for s in DocumentSchema]
    except ImportError:
        chunk_vals = ["semantic", "fixed", "fixed_overlap", "agentic", "csv_row"]
        schema_vals = ["restaurant", "travel", "support"]
    search_modes = ["semantic", "keyword", "hybrid"]
    for t in tools_list:
        if t.get("name") == "search_documents":
            sch = t.get("parameters_schema") or {}
            enum = (sch.get("properties") or {}).get("search_mode", {}).get("enum")
            if enum:
                search_modes = enum
            break
    chunk_line = f"Chunk strategy (ingest): optional; values: {', '.join(chunk_vals)}. Optional: chunk_size, overlap (for fixed_overlap). CSV only: schema: {', '.join(schema_vals)}; for CSV use chunk_strategy csv_row or omit."
    search_line = f"Search (search_documents): optional search_mode: {', '.join(search_modes)} (default semantic); k (default 5)."
    return chunk_line + " " + search_line


def planner_node(
    state: AgentState,
    config: AgentConfig,
    registry: ToolRegistry,
    max_tool_steps: int = 10,
    system_prompt_override: Optional[str] = None,
    current_collection: Optional[str] = None,
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
    rag_options = _rag_options_blob(tools_list)
    current_collection_line = ""
    if current_collection:
        current_collection_line = f'Current collection for this session: "{current_collection}". All ingest and search use this collection. When the user asks which collection is in use or where data is being ingested, tell them "{current_collection}".'
    else:
        # Multi-collection: agent must choose collection by task via collection_name in tool calls
        current_collection_line = (
            'You can use multiple collections. Call list_collections to see available collection names; then pass "collection_name" when calling search_documents, ingest_file, or ingest_directory using one of those names. '
            'Use the collection that holds system documentation when the task is about the system itself (how the system works, RAG options, documentation, or planning). '
            'Use the collection for user data for user content, ingested files, and any other task (default). When the user asks which collection is in use, explain that you choose by task: system docs vs user data.'
        )

    if system_prompt_override is not None:
        system_prompt = system_prompt_override
    else:
        system_prompt = load_planner_prompt(
            tools_blob=tools_blob,
            rag_options=rag_options,
            current_collection_line=current_collection_line,
            max_tool_steps=max_tool_steps,
        )

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
            if ok and isinstance(result, dict):
                if name == "ingest_directory":
                    ingested = result.get("ingested_count")
                    if ingested is not None:
                        line += f", ingested_count={ingested}"
                elif name == "create_collection":
                    cname = result.get("collection_name")
                    purpose = result.get("purpose")
                    if cname:
                        line += f", collection_name={cname}"
                    if purpose:
                        line += f", purpose={purpose!r}"
            prior_context += line + "\n"
    conv_block = _format_message_history(state.get("message_history"))
    user_prompt = f"{conv_block}Query: {query}{prior_context}\n\nClassify intent and respond with JSON only."

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
        # Block repeated list_collections (one call is enough)
        if validated.get("intent") == "tool" and validated.get("tool_name") == "list_collections":
            for tc in tool_calls:
                if tc.get("tool_name") == "list_collections" and tc.get("ok") and tc.get("result") is not None:
                    # If we have list_collections but no search yet, and the user asked a content question, run search instead of direct
                    has_search = any(t.get("tool_name") == "search_documents" for t in tool_calls)
                    query = (state.get("query") or "").strip().lower()
                    content_question = not has_search and (
                        "tell me about" in query or "what is" in query or "how does" in query
                        or "according to" in query or "based on the" in query or "what can you" in query
                    )
                    if content_question:
                        res = tc.get("result")
                        collections = res.get("collections", res) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                        coll = collections[0] if collections else "artemis_user_docs"
                        logger.info(
                            "Blocking repeated list_collections; forcing search_documents so RAG lookup runs"
                        )
                        validated = {
                            **validated,
                            "intent": "tool",
                            "tool_name": "search_documents",
                            "tool_args": {"query": state.get("query", ""), "collection_name": coll},
                            "reasoning": "Collections already listed; running search_documents to retrieve document content for the answer.",
                        }
                    else:
                        logger.info(
                            "Blocking repeated list_collections; forcing intent=direct"
                        )
                        validated = {
                            **validated,
                            "intent": "direct",
                            "tool_name": None,
                            "tool_args": None,
                            "reasoning": "Collections already listed; answer with available context.",
                        }
                    break
        # Block duplicate ingest_directory only when the previous call actually succeeded (ingested_count > 0)
        if validated.get("intent") == "tool" and validated.get("tool_name") == "ingest_directory":
            new_args = validated.get("tool_args") or {}
            new_path = _normalize_path(new_args.get("directory_path") or "")
            for tc in tool_calls:
                if tc.get("tool_name") != "ingest_directory":
                    continue
                prev_result = tc.get("result")
                # Only treat as success: dict with ingested_count > 0 (wrapper returns list on collection error)
                if isinstance(prev_result, dict) and prev_result.get("ingested_count", 0) > 0:
                    pass
                else:
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
