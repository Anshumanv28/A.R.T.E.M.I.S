# RAG system usage

How to use the A.R.T.E.M.I.S. RAG system standalone and with the agent, including all RAG tools.

## Overview

The RAG (Retrieval-Augmented Generation) system lets you:

- **Ingest** supported data (CSV, PDF, DOCX, Markdown, plain text) into a vector store (Qdrant)
- **Retrieve** relevant chunks by semantic (or keyword/hybrid) search
- **Manage collections** (list, create, get info, clear, delete)

The same pipeline works when you call it directly (standalone) and when the agent uses it via callable tools (search, ingest, collection management).

## Prerequisites

- **Qdrant**: Running Qdrant instance (local Docker or [Qdrant Cloud](https://cloud.qdrant.io/))
- **Environment**: Set `QDRANT_URL` and optionally `QDRANT_API_KEY` (e.g. in `.env`)
- **Python**: Install project dependencies (see [requirements.txt](../requirements.txt)); `artemis.rag` uses `qdrant-client`, `sentence-transformers`, and ingestion/loader libs as needed

## Standalone use

1. **Create an Indexer** (manages embedder and Qdrant connection):

   ```python
   from artemis.rag.core import Indexer

   indexer = Indexer(collection_name="my_docs")
   ```

2. **Ingest files** (reuse the same indexer for multiple files):

   ```python
   from artemis.rag.ingestion import ingest_file, FileType

   ingest_file("document.pdf", FileType.PDF, indexer)
   ingest_file("notes.txt", FileType.TEXT, indexer)
   ingest_file("data.csv", FileType.CSV, indexer)
   ```

   Or use helpers: `ingest_pdf`, `ingest_text`, `ingest_md`, `ingest_docx`, `ingest_csv`.

3. **Create a Retriever** (use the same indexer so the embedder and collection match):

   ```python
   from artemis.rag.core import Retriever, RetrievalMode

   retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
   ```

4. **Retrieve**:

   ```python
   results = retriever.retrieve("your query", k=5)
   # Each result: {"text", "score", "metadata"}
   ```

For more detail on the pipeline and parameters, see [ARCHITECTURE_FLOW.md](ARCHITECTURE_FLOW.md) and [examples (e.g. PDF RAG)](examples/README_PDF_RAG.md).

## Using RAG with the agent

The agent uses RAG **via a central tool registry**; there is **no dedicated RAG node**. The planner chooses either a **tool** (e.g. `search_documents`, `ingest_file`, `suggest_ingest_options`) or **direct** answer. When the planner selects `search_documents`, the tool node runs it and the direct-answer node synthesizes from the results. RAG is one set of tools among others—the agent is not hard-wired to a single retrieval path.

**Default: multi-collection.** If you call `run_agent(query)` without passing `retriever` or `indexer`, the agent runs with two collections: `artemis_system_docs` (for system/docs/RAG questions) and `artemis_user_docs` (for user data). The planner is instructed to pass `collection_name` in tool calls so the agent can switch by task. Ingest system documentation into `artemis_system_docs` so the agent can answer “how does the agent work?” from the docs. Use `run_agent(..., retriever=r, indexer=i)` or the CLI flag `--single-collection` when you want a single collection for everything.

1. **Multi-collection (default):** `run_agent("What is the main topic?")` — no retriever/indexer; registry is built with `artemis_system_docs` and `artemis_user_docs`.
2. **Single-collection:** Create `Indexer` and `Retriever`, optionally ingest, then `run_agent("What is the main topic?", retriever=retriever, indexer=indexer)`.

   ```python
   from artemis.agent import run_agent
   from artemis.rag.core import Indexer, Retriever, RetrievalMode

   indexer = Indexer(collection_name="my_docs")
   retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
   result = run_agent("What is the main topic?", retriever=retriever, indexer=indexer)
   print(result["final_answer"])
   ```

You can also pass a pre-built `ToolRegistry` via `run_agent(..., registry=my_registry)`. See [Agent architecture](AGENT_ARCHITECTURE.md) and [Agent quick start](AGENT_QUICKSTART.md).

## RAG tools for the agent

The agent uses a **central tool registry**. `run_agent` builds a registry and registers the following RAG tools by default (from `artemis.rag.tools`), so the planner can choose when to search, ingest, or manage collections. There is no special RAG path—RAG is invoked when the planner selects the appropriate tool.

| Tool | Purpose |
|------|---------|
| **search_documents** | Search the knowledge base; returns `list[dict]` with `text`, `score`, `metadata`. Optional `collection_name` (multi-collection), `search_mode` (semantic, keyword, hybrid), `k`. |
| **ingest_file** | Ingest a file by path and file type. Optional `collection_name`, `chunk_strategy`, `chunk_size`, `overlap`; for CSV: `schema`. |
| **ingest_directory** | Ingest all files in a directory by extension. Optional `collection_name`, chunk params. Supports `llm_client` for agentic chunking. |
| **suggest_ingest_options** | Returns recommended `file_type`/`file_extension`, `chunk_strategy`, `chunk_size`, `overlap` (and CSV `schema` when applicable) for a given path. Call before ingest when the user asks for best options or “don’t ingest, just suggest.” |
| **get_rag_options** | Returns available `search_modes`, `chunk_strategies`, `csv_schemas`, and (in multi-collection mode) `collections` and `collection_usage`. |
| **list_collections** | List all Qdrant collection names (uses env for Qdrant URL/API key). |
| **get_collection_info** | Get info (e.g. points count, status) for a collection by name. |
| **create_collection** | Create a new collection (optional embedding dimension). |
| **clear_collection** | Remove all points from a collection; **requires `confirm=True`**. |
| **delete_collection** | Delete a collection entirely; **requires `confirm=True`**. |

### Safety for destructive operations

`clear_collection` and `delete_collection` in [collection_manager](../artemis/rag/core/collection_manager.py) already require `confirm=True`. The tool wrappers pass through a `confirm` argument. When binding these tools for the agent:

- Only set `confirm=True` **after the user has explicitly approved** the action (e.g. in your UI or conversation flow).
- Do not let the agent set `confirm` on its own; treat it as an application-level safety check.

### Example: binding the search tool

```python
from artemis.rag import Retriever, RetrievalMode, Indexer, create_rag_search_tool

indexer = Indexer(collection_name="my_docs")
retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
search_fn = create_rag_search_tool(retriever, k=5)
# Register search_fn as a tool in your tool-calling node
# When the agent calls it with a query string, it returns a list of result dicts.
```

### Example: binding the ingest tool

```python
from artemis.rag import Indexer, create_rag_ingest_tool

indexer = Indexer(collection_name="my_docs")
ingest_fn = create_rag_ingest_tool(indexer)
# ingest_fn(path: str, file_type: str) -> dict
# file_type one of: "csv", "pdf", "docx", "md", "text"
```

### Example: collection management tools

```python
from artemis.rag.tools import (
    list_collections_tool,
    get_collection_info_tool,
    create_collection_tool,
    clear_collection_tool,
    delete_collection_tool,
)

list_fn = list_collections_tool()           # () -> list[str]
info_fn = get_collection_info_tool()       # (collection_name: str) -> dict
create_fn = create_collection_tool()       # (collection_name: str, embedding_dim?: int) -> bool
clear_fn = clear_collection_tool()         # (collection_name: str, confirm: bool) -> bool
delete_fn = delete_collection_tool()       # (collection_name: str, confirm: bool) -> bool
```

Use the same Qdrant env vars (`QDRANT_URL`, `QDRANT_API_KEY`) as the rest of your app so the agent operates on the same vector store.

## RAG options and extending strategies

The agent’s search and ingest tools expose **search modes** (e.g. semantic, keyword, hybrid) and **chunk strategies** (e.g. semantic, fixed, fixed_overlap, agentic, csv_row) plus optional parameters like `chunk_size`, `overlap`, and CSV `schema`. These options are **derived from the RAG registries** at runtime:

- **Automatic:** Add a new chunk or retrieval strategy in code and register it with the appropriate decorator (`@register_chunker`, `@register_strategy`, or `@register_csv_schema`). After restart, the agent sees the new option with no changes to the agent or tool-registry code.
- **Manual:** You can override or restrict the options the agent sees (e.g. a fixed list of strategies or a config filter).

The user can ask the agent “What search strategies do you have?” or “What chunking options are available?”; the planner can call the **get_rag_options** tool (no arguments) to return the current list programmatically. For full details on adding or restricting strategies, see [RAG customization](RAG_CUSTOMIZATION.md#5-adding-new-strategies-automatic-vs-manual).
