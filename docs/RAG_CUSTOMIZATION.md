# RAG System Customization Reference

This document lists **all parameters the RAG system already supports** for ingestion, chunking, and retrieval. Use it to know what can be exposed to the agent or to users.

**Optional: Agent enrichment.** You can ingest this document (or a short “RAG guide”) into your knowledge base if you want the agent to be able to search for detailed guidance (e.g. when to use semantic vs fixed_overlap). The agent does **not** require this for correct use of ingest/search; RAG options are exposed via the tool schema and planner prompt. Ingest RAG_CUSTOMIZATION only when you want the agent to answer “when should I use X?” from retrieved text.

---

## 1. Ingestion (entry point)

**API:** `ingest_file(path, file_type, indexer, chunk_strategy=None, schema=None, **chunk_kwargs)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str / Path | — | Path to the file. |
| `file_type` | `FileType` | — | One of: `csv`, `pdf`, `docx`, `md`, `text`. |
| `indexer` | `Indexer` | — | Indexer instance (collection, embedder, Qdrant). |
| `chunk_strategy` | `ChunkStrategy` or None | Per-file default (see below) | Override chunking strategy. |
| `schema` | `DocumentSchema` or None | None | **CSV only.** Schema for row→document conversion. |
| `**chunk_kwargs` | Any | — | Passed to the chunker (e.g. `chunk_size`, `overlap`). |

**Default chunk strategy by file type** (`DEFAULT_CHUNK_FOR_FILETYPE`):

- CSV → `csv_row`
- PDF, DOCX, TEXT → `fixed_overlap`
- MD → `semantic`

**Convenience functions:** `ingest_csv`, `ingest_pdf`, `ingest_docx`, `ingest_md`, `ingest_text` — same options, file type fixed.

---

## 2. Chunking strategies and their parameters

Chunkers are selected by `chunk_strategy`; `chunk_kwargs` are forwarded to the chosen chunker.

### 2.1 `ChunkStrategy.CSV_ROW` (CSV only)

**Chunker:** `csv_row_chunker(df, schema=None, csv_path=None)`

- `schema`: Optional `DocumentSchema`. If set, uses a registered converter (e.g. `DocumentSchema.RESTAURANT`, `DocumentSchema.TRAVEL`, `DocumentSchema.SUPPORT`). Requires `csv_path`.
- `csv_path`: Required when `schema` is set (ingestion passes `path`).
- No `chunk_size`/`overlap` — one document per row.

**DocumentSchema values:** `restaurant`, `travel`, `support` (extensible via `register_csv_schema`).

### 2.2 `ChunkStrategy.FIXED`

**Chunker:** `fixed_chunker(text, chunk_size=1000)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | int | 1000 | Target chunk size in characters (word-boundary aware). |

### 2.3 `ChunkStrategy.FIXED_OVERLAP`

**Chunker:** `fixed_overlap_chunker(text, chunk_size=800, overlap=200)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | int | 800 | Target chunk size in characters. |
| `overlap` | int | 200 | Overlap between consecutive chunks. |

### 2.4 `ChunkStrategy.SEMANTIC`

**Chunker:** `semantic_chunker(text, chunk_size=1000, respect_paragraphs=True, respect_markdown=True, embedder=None)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | int | 1000 | Target size; respects sections/paragraphs when possible. |
| `respect_paragraphs` | bool | True | Prefer paragraph boundaries. |
| `respect_markdown` | bool | True | For MD, split by heading sections first. |
| `embedder` | Embedder or None | None | Optional; not yet used for grouping. |

### 2.5 `ChunkStrategy.AGENTIC`

**Chunker:** `agentic_chunker(text, chunk_size=1000, llm_client=None)`

- When **`llm_client` is provided** and the text length is within the LLM limit (~6000 characters), the chunker uses the LLM to split the text into semantic chunks (one topic/section per chunk). The LLM returns a JSON array of chunk strings; the original text is preserved.
- When `llm_client` is **None**, or the text is too long, or the LLM call fails, the chunker **falls back** to fixed-overlap chunking so ingestion always succeeds.
- `chunk_size`: used by the fallback; also passed when calling the LLM for consistency.
- **Agent use:** For `ingest_directory` with `chunk_strategy="agentic"`, the agent tool layer passes an LLM client into the directory ingest so agentic (LLM) chunking is used when applicable. Single-file ingest can pass `llm_client` via `chunk_kwargs` if the caller provides it.

---

## 3. Retrieval (search)

### 3.1 Retriever construction

**API:** `Retriever(mode=..., indexer=None, embedder=None, qdrant_url=..., qdrant_api_key=..., collection_name="artemis_documents", metadata_config=None)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `RetrievalMode` | `SEMANTIC` | `semantic`, `keyword`, or `hybrid`. |
| `indexer` | Indexer or None | None | Preferred: supplies embedder, Qdrant client, collection. |
| `embedder` | Embedder or None | None | Required if no indexer and mode is semantic/hybrid. |
| `qdrant_url` / `qdrant_api_key` | str | env | Used when indexer is None. |
| `collection_name` | str | `"artemis_documents"` | Qdrant collection name. |
| `metadata_config` | MetadataConfig or None | None | Optional field mappings/aliases. |

### 3.2 Retrieval modes

| Mode | Value | Description |
|------|--------|-------------|
| `RetrievalMode.SEMANTIC` | `"semantic"` | Vector similarity (embedding). |
| `RetrievalMode.KEYWORD` | `"keyword"` | BM25 keyword search (requires `rank_bm25`). |
| `RetrievalMode.HYBRID` | `"hybrid"` | Semantic + keyword combined (weights 0.7 / 0.3 internally). |

### 3.3 Retrieve call

**API:** `retriever.retrieve(query, k=5)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | — | Search query. |
| `k` | int | 5 | Number of documents to return. |

**Note:** Strategy-internal options (e.g. hybrid’s semantic_weight/keyword_weight, or internal `semantic_k`/`keyword_k`) are not currently exposed on `retrieve()`; they are fixed inside each strategy.

---

## 4. Summary: what can be added for the agent

From the above, these are the **existing** knobs that could be exposed as agent (or user) parameters:

**Ingestion / chunking**

- `chunk_strategy`: `semantic` \| `fixed` \| `fixed_overlap` \| `agentic` (and `csv_row` for CSV only).
- `chunk_size`: int (for fixed, fixed_overlap, semantic, agentic).
- `overlap`: int (for fixed_overlap only).
- `respect_paragraphs` / `respect_markdown`: bool (for semantic only).
- `schema`: for CSV only — `restaurant` \| `travel` \| `support` (or any registered schema).

**Retrieval**

- `search_mode`: `semantic` \| `keyword` \| `hybrid` — per-request via the `search_documents` tool (default `semantic`). The list of available modes is derived from the retrieval registry at runtime.
- `k`: int (already in the search tool; default 5).

**Not yet exposed at API level**

- Hybrid weights (semantic_weight, keyword_weight).
- Internal semantic_k / keyword_k in hybrid.
- Embedder or metadata_config (advanced; usually not agent-tunable).

**Agent tools**

- The agent’s tool schemas and planner “RAG options” blob are **derived from** the chunk and retrieval registries (see §5). The agent can also call `get_rag_options` (no arguments) to return the current list of search modes, chunk strategies, and CSV schemas programmatically.

This document reflects the code as of the last update; when adding agent parameters, align them with these APIs so the agent drives the same RAG customization the system already supports.

---

## 5. Adding new strategies: automatic vs manual

The agent learns which RAG options exist in two ways: **automatically from registries** (recommended) or **manually** by overriding or restricting what is exposed.

### 5.1 Automatic method (registry-driven)

**Principle:** Registries are the single source of truth. Tool parameter enums and the planner’s RAG options blob are **derived from** the chunk and retrieval registries. When you add and register a new strategy in code, the agent sees it after a restart with no changes to agent or tool-registry code.

**Chunking strategies**

1. Add a new value to the `ChunkStrategy` enum in [artemis/rag/ingestion/chunkers/registry.py](../artemis/rag/ingestion/chunkers/registry.py) (if you need a new name).
2. Implement a chunker function that returns `(documents, metadata)`.
3. Register it with the decorator:
   ```python
   from artemis.rag.ingestion.chunkers.registry import register_chunker, ChunkStrategy

   @register_chunker(ChunkStrategy.MY_STRATEGY)
   def my_chunker(raw, **kwargs):
       # ...
       return documents, metadata
   ```
4. Ensure the chunker module is imported (e.g. so the decorator runs). Restart the agent.
5. **Result:** The ingest tools’ `chunk_strategy` enum and the planner’s RAG options blob will include the new strategy automatically (they are built from `CHUNKERS.keys()`).

**CSV schemas**

1. Add a value to the `DocumentSchema` enum in [artemis/rag/ingestion/converters/csv_converter.py](../artemis/rag/ingestion/converters/csv_converter.py) if needed.
2. Implement a converter and register it with `@register_csv_schema(DocumentSchema.MY_SCHEMA)`.
3. Restart the agent. The ingest tool’s `schema` enum and planner blob are derived from `CSV_CONVERTERS.keys()`.

**Retrieval (search) modes**

1. Add a new value to the `RetrievalMode` enum in [artemis/rag/core/retriever.py](../artemis/rag/core/retriever.py).
2. Implement a strategy function with signature `(retriever, query, k) -> list[dict]` and register it:
   ```python
   from artemis.rag.core.retriever import register_strategy, RetrievalMode, Retriever

   @register_strategy(RetrievalMode.MY_MODE)
   def my_search_strategy(retriever: Retriever, query: str, k: int):
       # ...
       return results
   ```
3. Ensure the strategy module is imported (e.g. in [artemis/rag/strategies/__init__.py](../artemis/rag/strategies/__init__.py)). Restart the agent.
4. **Result:** [run_agent](../artemis/agent/run.py) builds the `retrievers` dict by iterating over `RETRIEVAL_STRATEGIES`. For each registered mode it tries to create a `Retriever(mode=..., indexer=idx)`; if that succeeds, the mode is added. The `search_documents` tool’s `search_mode` enum is derived from the keys of that dict, so the new mode appears automatically. Modes that require extra dependencies (e.g. `keyword` and `hybrid` require `rank_bm25`) are only added when those deps are available.

**Summary (automatic)**

| What you add        | Where to register                          | Agent sees it after |
|---------------------|--------------------------------------------|----------------------|
| Chunk strategy      | `@register_chunker(ChunkStrategy.X)`       | Restart              |
| CSV schema          | `@register_csv_schema(DocumentSchema.X)`   | Restart              |
| Retrieval mode      | `@register_strategy(RetrievalMode.X)`      | Restart (if Retriever builds successfully for that mode) |

No edits to the agent, the tool registry builder, or the planner prompt are required.

### 5.2 Manual method (override or restrict)

If you want to **restrict** or **override** what the agent sees (e.g. only a subset of strategies, or different labels), you can do so in one of these ways:

**Fully manual**

- Ignore the registry-driven derivation. In the code that builds the RAG tool registry (e.g. [artemis/agent/tools/__init__.py](../artemis/agent/tools/__init__.py) `build_rag_registry`), pass or maintain your own lists for `chunk_strategy` enum, `schema` enum, and/or the `retrievers` dict. The planner prompt’s RAG options blob can be hand-written to match. The agent then only sees the options you define.

**Override on top of derivation**

- Keep deriving from registries by default, but add an optional config or parameter (e.g. `agent_chunk_strategies: ["semantic", "fixed"]` or `agent_search_modes: ["semantic"]`) that filters or overrides the derived lists. When that config is set, the tool schemas and planner blob use the restricted list instead of the full registry. When unset, behavior remains fully registry-driven.

**When to use manual**

- Limit the agent to a subset of strategies for safety or simplicity.
- Expose different names or ordering than the registry.
- Support a deployment where not all strategies are enabled (e.g. no keyword/hybrid if BM25 is not installed, which is already handled by the automatic logic; manual override can further restrict to only `semantic` if desired).
