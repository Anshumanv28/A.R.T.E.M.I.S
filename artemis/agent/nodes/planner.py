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
            'You can use multiple collections. Always pass "collection_name" when calling search_documents, ingest_file, or ingest_directory. '
            'Use artemis_system_docs when the task is about the system itself: how the system works, RAG options, documentation, or planning decisions. '
            'Use artemis_user_docs for user data, ingested content, and any other task (default). When the user asks which collection is in use, explain that you choose by task: system docs vs user data.'
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
Available tools:
{tools_blob}

RAG options (quick reference): {rag_options}
For detailed RAG guidance (when to use which strategy), the user may have ingested RAG documentation; you can search for it if the user asks for advice.
{current_collection_line}

Your task: decide whether to call ONE tool (intent="tool") or to answer the user directly (intent="direct").

Use intent="tool" when:
- The user asks how THIS system/agent works (e.g. "how does the A.R.T.E.M.I.S agent decide when to use a tool?", "what is the agent graph flow?", "what nodes does the agent have?", "how does the planner work?", "how does RAG/chunking work in this project?", "according to the documentation", "based on the system docs"). You MUST call search_documents with collection_name "artemis_system_docs" and a query that matches the question—do NOT answer from general knowledge; the answer must come from the ingested system docs.
- The user needs to search the knowledge base (use search_documents with query). Use collection_name "artemis_system_docs" for system/docs/architecture questions, "artemis_user_docs" for user data.
- The user explicitly asks to ingest a specific file or directory (e.g. "ingest docs/", "add this file to the KB"). When ingesting: if you do not yet have recommended options for that path, call suggest_ingest_options with that path first; on the next step use ingest_file or ingest_directory with the returned chunk_strategy, file_type/file_extension, chunk_size, overlap (and schema for CSV) so the ingest uses the best options for the data.
- The user wants to list collections, get collection info, create/clear/delete collections.
- The user asks what search or chunking options are available (use get_rag_options).
- The user asks only for suggestions or recommendations for a path (e.g. "what are the best options for ingesting docs?", "suggest settings for this folder", "don't ingest, just tell me what you'd use", "what would be the best way to ingest X?"). Call suggest_ingest_options with that path; then on the next step answer with the returned options—do NOT call ingest_file or ingest_directory.
- You need information from a tool before you can answer (e.g. suggest_ingest_options to get options before ingest; or search_documents to answer about this system).

Use intent="direct" when:
- You already have search_documents (or other tool) results in the conversation that contain the answer—then answer from that context.
- The user query is conversational or doesn't require any tool (greetings, off-topic). Do NOT use direct for "how does the agent work?", "what is the graph/planner/nodes?" or any question about this system unless you already have search results from artemis_system_docs to answer from.
- The user asks for a suggestion, advice, or "what are my options" about ingestion in general (e.g. "how should I ingest?", "what chunking do you suggest?") without naming a path—answer with available options or use get_rag_options, then answer. Do NOT call ingest when they only want advice.
- You already have suggest_ingest_options results and the user only wanted suggestions (not to actually ingest); summarize the recommended options and do not call ingest_file or ingest_directory.
- Only call ingest when the user explicitly asks to ingest a specific path (e.g. "ingest docs/", "add this file to the KB").
- You have already gathered enough information from previous tool calls.
- You have already run ingest_directory successfully for a directory (do not call ingest_directory again for the same directory).
- You have already run search_documents and got results (use intent=direct to answer; do not call search_documents again).

Call ingest_directory at most once per directory per user request. After search_documents has returned results, use intent=direct to answer; do not call search_documents again. After a successful ingest_directory (ingested_count > 0), use intent="direct" to confirm or answer; do not call ingest_directory again for the same path.

You have at most {max_tool_steps} tool calls total; when in doubt, move to direct.

Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{"intent": "tool" or "direct", "tool_name": "<name>" (only if intent is tool), "tool_args": {{}} (only if intent is tool, with the right parameters), "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

For search_documents use tool_args like {{"query": "user query here", "k": 5}} or add "search_mode": "keyword"/"hybrid" if needed. If the tool accepts collection_name, ALWAYS use "collection_name": "artemis_system_docs" when the user asks about how this agent/system works (planner, graph, nodes, RAG, chunking, architecture); use "artemis_user_docs" for user data and general content queries.
When the user asks to ingest a path or directory: first call suggest_ingest_options with {{"path": "path or directory they gave"}} to get recommended options; then call ingest_file or ingest_directory using the returned file_type/file_extension, chunk_strategy, chunk_size, overlap (and schema for CSV). This ensures ingest uses the best strategy for the data.
For suggest_ingest_options use {{"path": "path or directory"}} (optional "path_type": "file" or "directory"). If the user asked to actually ingest, use the returned options in your next ingest_file or ingest_directory call. If the user asked only for suggestions (e.g. "don't ingest, just suggest", "what are the best options for X?"), call suggest_ingest_options and then answer with the recommendations—do not call ingest.
For ingest_file use when the user asks to ingest a specific file. Prefer options from suggest_ingest_options. Use {{"path": "/path/to/file", "file_type": "pdf"}} and include chunk_strategy, chunk_size, overlap from suggestions; for CSV add schema if suggested. If the tool accepts collection_name, use "artemis_user_docs" for user data.
For ingest_directory use when the user asks to ingest a specific directory. Prefer options from suggest_ingest_options. Use {{"directory_path": "path", "file_extension": "md"}} and include chunk_strategy, chunk_size, overlap from suggestions. If the tool accepts collection_name, use "artemis_user_docs" for user content.
For list_collections use {{}}.
For get_rag_options use {{}} to return available search modes and chunk strategies (use when the user asks what RAG options or search strategies are available).
For get_collection_info use {{"collection_name": "name"}}.
For create_collection use {{"collection_name": "name"}} or {{"collection_name": "name", "embedding_dim": 384}}.
For clear_collection/delete_collection use {{"collection_name": "name", "confirm": true}} (only after user confirmed).

Default collection: When the run has a single collection, it is the "current collection" above. When you have multiple collections (artemis_system_docs and artemis_user_docs), always pass collection_name in tool args: use artemis_system_docs for system/docs/RAG/planning; use artemis_user_docs for user data and everything else (default). For get_collection_info, clear_collection, delete_collection use the specific collection name the user meant, or "artemis_documents" / "artemis_user_docs" if they said "the collection" or "the RAG collection".

Collection usage: When the tools accept collection_name, choose by task: artemis_system_docs = how the system works, RAG options, documentation, planning; artemis_user_docs = user content, ingested files, general queries. Use search_mode semantic for conceptual questions and keyword for exact terms; k=5 or more for broader context. Chunking: semantic, fixed, fixed_overlap, agentic, csv_row (CSV). Retrieval: search_mode semantic | keyword | hybrid; k = number of chunks. CSV schema: restaurant, travel, support when applicable.
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
