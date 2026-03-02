"""
Direct answer node for queries that don't need tools or to synthesize from tool results.

Uses tool_calls_summary and formatted tool results (e.g. search docs) as context
when present, so the prompt stays focused instead of dumping raw tool_calls.
"""

from typing import Any, Dict, List, Optional

from artemis.agent.state import AgentState
from artemis.agent.config import AgentConfig
from artemis.agent.prompts import load_direct_answer_prompt
from artemis.agent.llm.groq_client import GroqClient
from artemis.agent.llm.openai_client import OpenAIClient
from artemis.utils import get_logger

logger = get_logger(__name__)


# Max chars per document chunk in context to avoid Groq 413 (request too large)
_MAX_CHARS_PER_DOC = 800
# Max conversation turns to include (2 exchanges = 4 messages); truncate assistant to this many chars
_MAX_MESSAGE_HISTORY = 4
_MAX_ASSISTANT_CHARS = 400


def _format_message_history(history: Optional[List[Dict[str, Any]]]) -> str:
    """Format message_history for prompt context."""
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


def _format_documents(docs: List[Dict[str, Any]], max_chars_per_doc: int = _MAX_CHARS_PER_DOC) -> str:
    """Format document list for LLM context (text, score, metadata). Truncates long chunks."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        text = doc.get("text", "")
        if max_chars_per_doc and len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc].rstrip() + "..."
        score = doc.get("score", 0.0)
        entry = f"[{i}] (Score: {score:.4f})\n{text}"
        metadata = doc.get("metadata", {})
        if metadata:
            meta_str = ", ".join(f"{k}={v}" for k, v in metadata.items() if k != "text")
            if meta_str:
                entry += f"\nMetadata: {meta_str}"
        formatted.append(entry)
    return "\n\n".join(formatted)


def _build_tool_context(state: AgentState) -> str:
    """
    Build a short, focused context from tool_calls for the direct_answer prompt.
    Uses tool_calls_summary and formats any search-like results (list of doc dicts) for synthesis.
    When tool_calls is empty but tool_calls_summary is set (e.g. Supervisor passed reference info like tool list), include that.
    """
    tool_calls = state.get("tool_calls") or []
    summary = state.get("tool_calls_summary") or ""
    if not tool_calls:
        if summary:
            return "Context:\n" + summary
        return ""

    parts = []
    if summary:
        parts.append("Summary of tool calls:\n" + summary)

    # Only include the first search_documents result to avoid token overflow (Groq 413)
    search_documents_included = False
    for i, tc in enumerate(tool_calls, 1):
        name = tc.get("tool_name", "?")
        result = tc.get("result")
        ok = tc.get("ok", True)
        if not ok or result is None:
            continue
        if isinstance(result, list):
            # Search results: list of {text, score, metadata} (or empty)
            if result and isinstance(result[0], dict) and any("text" in r for r in result):
                if name == "search_documents" and search_documents_included:
                    continue
                if name == "search_documents":
                    search_documents_included = True
                parts.append(f"\nTool '{name}' returned the following documents:\n" + _format_documents(result))
            elif name == "search_documents" and len(result) == 0:
                parts.append(f"\nTool '{name}' returned no documents (knowledge base has no matching results for this query).")
            elif name == "list_collections":
                # Result may be list (legacy) or dict with "collections" and "purposes"
                if isinstance(result, dict):
                    names = [str(x) for x in result.get("collections", [])]
                    purposes = result.get("purposes") or {}
                else:
                    names = [str(x) for x in result]
                    purposes = {}
                if not names:
                    parts.append(
                        f"\nTool '{name}' returned no collections. The user may need to create a collection or ingest documents first."
                    )
                else:
                    lines = [f"\nTool '{name}' returned {len(names)} collection(s). Use these names for collection_name in search_documents, ingest_file, or ingest_directory:"]
                    for n in names:
                        desc = purposes.get(n)
                        if desc:
                            lines.append(f"  - {n}: {desc}")
                        else:
                            lines.append(f"  - {n}")
                    parts.append("\n".join(lines))
            elif result:
                parts.append(f"\nTool '{name}' result (list): {result}")
        elif isinstance(result, dict) and result:
            if name == "list_collections":
                names = [str(x) for x in result.get("collections", [])]
                purposes = result.get("purposes") or {}
                if not names:
                    parts.append(
                        f"\nTool '{name}' returned no collections. The user may need to create a collection or ingest documents first."
                    )
                else:
                    lines = [f"\nTool '{name}' returned {len(names)} collection(s). Use these names for collection_name in search_documents, ingest_file, or ingest_directory:"]
                    for n in names:
                        desc = purposes.get(n)
                        if desc:
                            lines.append(f"  - {n}: {desc}")
                        else:
                            lines.append(f"  - {n}")
                    parts.append("\n".join(lines))
            else:
                parts.append(f"\nTool '{name}' result: {result}")
        elif isinstance(result, str) and result:
            parts.append(f"\nTool '{name}' result: {result[:500]}")

    if not parts:
        return ""
    return "\n".join(parts).strip()


def direct_answer_node(state: AgentState, config: AgentConfig) -> AgentState:
    """
    Generate final answer: either direct (no tools) or synthesize from tool results.

    When tool_calls is non-empty, uses pre-summarized tool_calls_summary and
    formatted tool results (e.g. search docs) as context instead of raw dump.
    """
    query = state.get("query", "")

    if not query:
        logger.warning("Empty query in direct answer node")
        return {
            **state,
            "final_answer": "I need a query to provide an answer.",
            "error": "Empty query",
        }

    logger.info(f"Direct answer node processing query: '{query[:50]}...'")

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

    tool_context = _build_tool_context(state)
    conv_block = _format_message_history(state.get("message_history"))
    if tool_context:
        system_prompt = load_direct_answer_prompt(with_context=True)
        user_prompt = f"""{conv_block}Query: {query}

{tool_context}

Provide a comprehensive answer to the query based on the context above."""
    else:
        system_prompt = load_direct_answer_prompt(with_context=False)
        user_prompt = conv_block + ("Query: " + query if conv_block else query)

    try:
        final_answer = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        logger.info(f"Generated direct answer ({len(final_answer)} chars)")
        return {
            **state,
            "final_answer": final_answer,
            "retrieved_docs": state.get("retrieved_docs") or [],
        }
    except Exception as e:
        logger.exception(f"Error generating direct answer: {e}")
        return {
            **state,
            "final_answer": f"I encountered an error while generating an answer: {str(e)}",
            "error": f"Direct answer error: {str(e)}",
        }
