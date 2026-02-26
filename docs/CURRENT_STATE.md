# Current state of the system

High-level snapshot of what exists and where it lives (as of the last update).

## What’s implemented

### Agent (LangGraph)

- **Graph**: Three nodes only — **planner** → **tool_node** | **direct_answer**. No dedicated RAG node; RAG is invoked when the planner selects tools (e.g. `search_documents`, `ingest_file`).
- **Planner** (`artemis/agent/nodes/planner.py`): Classifies intent (tool vs direct), outputs `tool_name` + `tool_args` when tool. Uses a long inline system prompt; validates JSON; falls back to direct on parse error or step limit.
- **Tool node** (`artemis/agent/nodes/tool_node.py`): Dispatches by name via `ToolRegistry`; appends result to `tool_calls`; returns to planner.
- **Direct answer** (`artemis/agent/nodes/direct_answer.py`): Synthesizes final answer from query and tool results (e.g. search docs); uses short inline system prompts (with/without context).
- **State**: `query`, `tool_calls`, `tool_calls_summary`, `intent`, `final_answer`, `step_count`, etc. No top-level `retrieved_docs`; docs live inside `tool_calls` entries.
- **Run**: `run_agent(query, ...)` and CLI `python -m artemis.agent.run`. Default is **multi-collection** (`artemis_system_docs` + `artemis_user_docs`); optional `--single-collection` with `--collection name`.

### Tool registry

- **Generic registry** (`artemis/agent/tools/registry.py`): `ToolRegistry` + `ToolDescriptor` (name, description, parameters_schema, callable). Used by planner (list_tools) and tool_node (get + call).
- **RAG tools** (currently in `artemis/agent/tools/__init__.py`): `build_rag_registry(...)` builds a registry and registers RAG-only tools: `search_documents`, `ingest_file`, `ingest_directory`, `suggest_ingest_options`, `get_rag_options`, `list_collections`, `get_collection_info`, `create_collection`, `clear_collection`, `delete_collection`. Single- or multi-collection; agentic chunking when LLM client passed.

### RAG system (standalone + used by agent)

- **Core** (`artemis/rag/`): Indexer, Retriever, Embedder, collection_manager; ingestion (`ingest_file`, chunkers, loaders, converters); retrieval strategies (semantic, keyword, hybrid). Implementations live under `artemis/rag/core/`, `artemis/rag/ingestion/`, `artemis/rag/strategies/`.
- **RAG tools** (`artemis/rag/tools.py`): Thin wrappers for the agent: `create_rag_search_tool`, `create_rag_ingest_tool`, `create_rag_ingest_directory_tool`, `suggest_ingest_options`, list/get/create/clear/delete collection tools. The **agent** layer (`build_rag_registry`) wires these into a `ToolRegistry` with schemas and multi-collection routing.

### Prompts

- **Planner**: One long system prompt built as an f-string in `planner_node()` (role, tools list, RAG options, when tool vs direct, collection rules, JSON format).
- **Direct answer**: Two short system prompts inline in `direct_answer_node()` — one when there is tool context (cite [1],[2], say when context is missing), one when there is no context (helpful assistant, say when you don’t know).

### Configuration

- **Agent**: `AgentConfig` (provider, model, API keys, temperature, max_tokens, retrieval_k) from env or constructor. LLM clients: Groq, OpenAI.
- **RAG**: Qdrant URL/API key from env; embedder, chunk strategies, retrieval modes from registries.

## Where things live (code)

| Area            | Location |
|-----------------|----------|
| Agent graph     | `artemis/agent/graph.py` |
| Agent nodes     | `artemis/agent/nodes/` (planner, tool_node, direct_answer) |
| Agent config    | `artemis/agent/config.py` |
| Agent run/CLI   | `artemis/agent/run.py` |
| Tool registry   | `artemis/agent/tools/registry.py` |
| RAG tool wiring | `artemis/agent/tools/__init__.py` (`build_rag_registry`) |
| RAG core        | `artemis/rag/core/`, `artemis/rag/ingestion/`, `artemis/rag/strategies/` |
| RAG tool impl   | `artemis/rag/tools.py` |
| System prompts  | Inline in `planner.py` and `direct_answer.py` |

## Proposed layout (separation of concerns)

To keep RAG and prompts separate from future tools and features:

1. **System prompts** → `artemis/agent/prompts/`
   - Store planner and direct-answer system prompts in files (e.g. `.md` or `.txt`) with placeholders for dynamic parts.
   - Load and format in code so nodes stay thin and prompts are easy to edit and version.

2. **RAG tools** → `artemis/agent/tools/rag/`
   - Move all RAG-specific registration (e.g. `build_rag_registry`) into `artemis/agent/tools/rag/`.
   - Keep `artemis/agent/tools/registry.py` as the generic registry; `artemis/agent/tools/__init__.py` re-exports `ToolRegistry`, `ToolDescriptor`, and `build_rag_registry` from `tools.rag` for backward compatibility.
   - Future tool sets (e.g. weather, calendar) can live under `artemis/agent/tools/weather/`, `artemis/agent/tools/calendar/`, each registering into the same `ToolRegistry`.

Resulting structure:

```
artemis/agent/
  prompts/           # System prompts (planner, direct_answer)
    planner_system.md
    direct_answer_with_context.md
    direct_answer_no_context.md
    __init__.py      # load_planner_prompt(), load_direct_answer_prompt()
  tools/
    registry.py      # ToolRegistry, ToolDescriptor (generic)
    rag/             # RAG-only tool registration
      __init__.py    # build_rag_registry()
    __init__.py      # Re-export registry + build_rag_registry from rag
```

This keeps “RAG system tools” and “system prompts” in their own directories and makes it clear where to add new tool bundles and prompt content later.
