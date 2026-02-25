# RAG system usage

How to use the A.R.T.E.M.I.S. RAG system standalone and with the agent, including all RAG tools.

## Overview

The RAG (Retrieval-Augmented Generation) system lets you:

- **Ingest** supported data (CSV, PDF, DOCX, Markdown, plain text) into a vector store (Qdrant)
- **Retrieve** relevant chunks by semantic (or keyword/hybrid) search
- **Manage collections** (list, create, get info, clear, delete)

The same pipeline works when you call it directly (standalone) and when the agent uses it (via the RAG node or via callable tools).

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

Use the **same** Indexer and Retriever for ingestion and for the agent:

1. Create `Indexer` and optionally ingest files (as above).
2. Create `Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)`.
3. Pass the retriever into the agent:

   ```python
   from artemis.agent import run_agent

   result = run_agent("What is the main topic?", retriever=retriever)
   print(result["final_answer"])
   ```

The planner node classifies the query; when it decides the intent is `"rag"`, the RAG node calls `retriever.retrieve(...)` and then the LLM synthesizes an answer with citations. So the agent already uses your RAG data when retrieval is needed.

## RAG tools for the agent

When you add a **tool-calling node** (or ReAct loop) to the agent, you can register the following as callable tools so the agent can perform the same RAG operations a user can.

All tools live in `artemis.rag.tools` and are thin wrappers around the existing RAG and collection-manager APIs.

| Tool | Factory / callable | Purpose |
|------|--------------------|---------|
| **Search** | `create_rag_search_tool(retriever, k=5)` | Search the knowledge base; returns `list[dict]` with `text`, `score`, `metadata`. |
| **Ingest** | `create_rag_ingest_tool(indexer)` | Ingest a file by path and file type (e.g. `"pdf"`, `"text"`, `"csv"`, `"md"`, `"docx"`). |
| **List collections** | `list_collections_tool()` | List all Qdrant collection names. Uses env for Qdrant URL/API key. |
| **Get collection info** | `get_collection_info_tool()` | Get info (e.g. points count, status) for a collection by name. |
| **Create collection** | `create_collection_tool()` | Create a new collection (optional embedding dimension). |
| **Clear collection** | `clear_collection_tool()` | Remove all points from a collection; **requires `confirm=True`**. |
| **Delete collection** | `delete_collection_tool()` | Delete a collection entirely; **requires `confirm=True`**. |

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
