# Agent Layer Quick Start Guide

The A.R.T.E.M.I.S agent is a LangGraph-based orchestration system that routes queries between **tool use** (e.g. RAG search, ingest) and **direct answer**. There is **no dedicated RAG node**—RAG is invoked when the planner selects the `search_documents` tool (or ingest/collection tools). The agent can use multiple collections and choose by task (system docs vs user data).

## Overview

The agent consists of:

- **Planner node** – Classifies intent: use one **tool** (e.g. `search_documents`, `ingest_directory`, `get_rag_options`) or answer **directly** (e.g. from prior tool results or general knowledge). When the user asks how the system works, the planner should choose `search_documents` on the system collection first.
- **Tool node** – Runs the chosen tool (search, ingest, list collections, etc.) and appends the result to state, then returns to the planner.
- **Direct-answer node** – Produces the final reply from the query and prior tool results (e.g. retrieved chunks, ingest outcome).

Default mode is **multi-collection**: `artemis_system_docs` (system/docs/RAG context) and `artemis_user_docs` (user data). The planner is instructed to pass `collection_name` when calling search/ingest so the agent can switch by task. Use `--single-collection` only when you want one collection for everything.

## Prerequisites

1. **Environment variables** – Set up your `.env` file:

   ```bash
   GROQ_API_KEY=your-groq-api-key
   # or OPENAI_API_KEY for OpenAI

   QDRANT_URL=your-qdrant-url
   QDRANT_API_KEY=your-qdrant-api-key
   ```

2. **Dependencies** – `pip install -e .`

3. **Documents** – For RAG answers, ingest documents (e.g. into `artemis_system_docs` or `artemis_user_docs`) or use the agent’s `ingest_file` / `ingest_directory` tools. See [PDF RAG Example](examples/README_PDF_RAG.md) and [Agent test prompts](AGENT_TEST_PROMPTS.md).

## Quick Start

### Default: multi-collection (recommended)

```python
from artemis.agent import run_agent

# No retriever/indexer: run_agent builds artemis_system_docs + artemis_user_docs
# and registers RAG tools. The agent chooses collection by task.
result = run_agent("What chunking strategies are available?")
print(result["final_answer"])
print("Intent:", result["intent"])
print("Tool calls:", len(result.get("tool_calls", [])))
```

### Single-collection (legacy)

```python
from artemis.agent import run_agent
from artemis.rag.core import Indexer, Retriever, RetrievalMode

indexer = Indexer(collection_name="my_documents")
retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
# ... optionally ingest files with indexer ...

result = run_agent(
    "What is the main topic of the documents?",
    retriever=retriever,
    indexer=indexer,
)
print(result["final_answer"])
```

### Command line

Interactive (default multi-collection):

```bash
python -m artemis.agent.run
```

Single query:

```bash
python -m artemis.agent.run "What is the main topic?"
```

Single-collection mode:

```bash
python -m artemis.agent.run --single-collection --collection my_documents "Your query"
```

Options: `--provider groq|openai`, `--model <name>`.

## How it works

### Flow

```
Start → Planner → [intent?]
                    ↓
         ┌─────────┴─────────┐
         │                    │
    intent=tool          intent=direct
         │                    │
         ↓                    ↓
    Tool node          Direct-answer node
    (search_documents,      │
     ingest_file, ...)      ↓
         │                  END
         ↓
    (loop back to Planner)
```

- **Planner** – Chooses one of: call a tool (`intent="tool"` with `tool_name` and `tool_args`) or answer now (`intent="direct"`). For questions about how this agent/system works, the planner is instructed to call `search_documents` with `collection_name: "artemis_system_docs"` first.
- **Tool node** – Runs `registry.get(tool_name).callable(**tool_args)`, appends result to `tool_calls`, increments `step_count`, returns to planner.
- **Direct-answer node** – Uses the query and a summary of `tool_calls` to generate `final_answer`, then END.

### RAG as tools

RAG is not a separate path. When the user needs to search or ingest, the planner selects:

- `search_documents` – with optional `collection_name`, `search_mode`, `k`
- `ingest_file` / `ingest_directory` – with optional `collection_name`, `chunk_strategy`, etc.
- `suggest_ingest_options` – get recommended options for a path before ingesting
- `get_rag_options` – list search modes and chunk strategies
- Collection tools: `list_collections`, `get_collection_info`, `create_collection`, etc.

The direct-answer node then uses the tool results (e.g. retrieved chunks) to synthesize the reply.

### State shape

```python
{
    "query": str,
    "intent": "tool" | "direct",
    "tool_name": str | None,
    "tool_args": dict | None,
    "tool_calls": list[dict],   # each: tool_name, tool_args, result, ok
    "step_count": int,
    "final_answer": str,
    "confidence": float,
    "reasoning": str,
    "error": str | None,
}
```

There is no top-level `retrieved_docs`; retrieved content appears inside the relevant `tool_calls` entry when the tool was `search_documents`.

## Configuration

### Environment variables

```bash
ARTEMIS_LLM_PROVIDER=groq
ARTEMIS_LLM_MODEL=llama-3.3-70b-versatile
ARTEMIS_MAX_TOKENS=2048
ARTEMIS_TEMPERATURE=0.7
ARTEMIS_RETRIEVAL_K=5
```

### Programmatic

```python
from artemis.agent import AgentConfig

config = AgentConfig.from_env(provider="openai", model_name="gpt-4o-mini")
result = run_agent("Your query", config=config)
```

## Advanced: custom registry

```python
from artemis.agent import run_agent, AgentConfig
from artemis.agent.tools import ToolRegistry, build_rag_registry

config = AgentConfig.from_env()
registry = build_rag_registry(
    retriever=my_retriever,
    indexer=my_indexer,
    default_k=5,
    retrievers=my_retrievers_by_mode,
    llm_client_for_agentic=my_llm,
)
result = run_agent("Your query", config=config, registry=registry)
```

For multi-collection, build the registry with `indexers`, `retrievers_by_collection`, and `default_collection` (see `run_agent` in `artemis/agent/run.py`).

## Troubleshooting

- **"GROQ_API_KEY not found"** – Set `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env`.
- **"Collection does not exist"** – Ingest documents first or use an existing collection name; in multi-collection mode collections are created on first ingest.
- **Agent says it doesn’t have information** – For questions about the system (planner, graph, RAG), ensure system docs are ingested into `artemis_system_docs` and the planner is calling `search_documents` with `collection_name: "artemis_system_docs"`. See [Agent architecture](AGENT_ARCHITECTURE.md) and [Agent test prompts](AGENT_TEST_PROMPTS.md).

## Next steps

- [Agent architecture](AGENT_ARCHITECTURE.md) – Planner–tool loop, registry, no dedicated RAG path
- [RAG usage](RAG_USAGE.md) – Standalone RAG and agent RAG tools (search, ingest, multi-collection)
- [Agent test prompts](AGENT_TEST_PROMPTS.md) – Example prompts and retrieval-test queries
