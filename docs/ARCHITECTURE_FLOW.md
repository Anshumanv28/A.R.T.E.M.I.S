# A.R.T.E.M.I.S. Architecture Flow

This document explains the flow of data through the A.R.T.E.M.I.S. system and what users can configure at each stage.

## Overview

A.R.T.E.M.I.S. follows a clear pipeline: **Load → Chunk → Index → Retrieve**

```
┌─────────┐      ┌──────────┐      ┌─────────┐      ┌──────────┐
│  File   │ ───> │ Chunker  │ ───> │ Indexer │ ───> │ Retriever│
│         │      │          │      │         │      │          │
│ (Input) │      │ (Split)  │      │ (Store) │      │ (Search) │
└─────────┘      └──────────┘      └─────────┘      └──────────┘
```

## Detailed Flow Diagram

### Ingestion Flow (File → Vector Store)

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER CODE (Ingestion)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Create Indexer                                          │
│ ───────────────────────                                         │
│ indexer = Indexer(                                              │
│     qdrant_url="...",        ← User configurable               │
│     collection_name="docs",   ← User configurable               │
│     embedder=Embedder(...)   ← User configurable (optional)     │
│ )                                                               │
│                                                                 │
│ • Creates Embedder (embedding model)                           │
│ • Connects to Qdrant (vector database)                         │
│ • Ensures collection exists                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Ingest File(s)                                          │
│ ───────────────────────                                         │
│ ingest_file(                                                    │
│     path="file.pdf",         ← User provides                   │
│     file_type=FileType.PDF,  ← User selects                    │
│     indexer=indexer,         ← User passes (reuse same!)       │
│     chunk_strategy=...,      ← User configurable (optional)    │
│     chunk_size=...,          ← User configurable (optional)    │
│     overlap=...,             ← User configurable (optional)    │
│     schema=...                ← User configurable (CSV only)    │
│ )                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Load File (automatic)                                   │
│ ───────────────────────                                         │
│ • Reads file based on file_type                                 │
│ • CSV → DataFrame                                               │
│ • PDF/DOCX/MD/TEXT → String                                     │
│                                                                 │
│ User configurable: None (automatic based on file_type)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Chunk Content (automatic or user-selected strategy)     │
│ ───────────────────────                                         │
│ • Selects chunking strategy (default or user-specified)        │
│ • Splits content into chunks                                    │
│ • Generates metadata for each chunk                             │
│                                                                 │
│ User configurable:                                              │
│ • chunk_strategy: ChunkStrategy enum (optional)                 │
│   - CSV_ROW (default for CSV)                                   │
│   - FIXED (fixed size)                                          │
│   - FIXED_OVERLAP (default for PDF/DOCX/TEXT)                   │
│   - SEMANTIC (default for MD)                                   │
│   - AGENTIC (LLM-driven)                                        │
│ • chunk_size: int (e.g., 800, 1500)                             │
│ • overlap: int (e.g., 200, 300)                                 │
│ • schema: DocumentSchema (CSV only: RESTAURANT, TRAVEL)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Index Documents (delegated to Indexer)                  │
│ ───────────────────────                                         │
│ indexer.add_documents(documents, metadata)                      │
│                                                                 │
│ • Generates embeddings using Indexer's embedder                 │
│ • Stores embeddings + metadata in Qdrant                        │
│ • Uses same collection from Indexer                             │
│                                                                 │
│ User configurable: None (uses Indexer's configuration)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Result: Documents stored in Qdrant                              │
│ ───────────────────────                                         │
│ • Collection: indexer.collection_name                           │
│ • Embeddings: Generated using indexer.embedder                  │
│ • Metadata: From chunker                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Retrieval Flow (Query → Results)

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER CODE (Retrieval)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Create Retriever                                        │
│ ───────────────────────                                         │
│ retriever = Retriever(                                          │
│     mode=RetrievalMode.SEMANTIC, ← User configurable            │
│     indexer=indexer,            ← Recommended (ensures consistency)
│     # OR (without indexer):                                     │
│     embedder=embedder,          ← Must match indexing embedder! │
│     qdrant_url="...",           ← Must match indexing config!  │
│     collection_name="docs"      ← Must match indexing config!  │
│ )                                                               │
│                                                                 │
│ RECOMMENDED: Pass indexer (guarantees consistency)             │
│ ALTERNATIVE: Pass embedder + qdrant_url + collection_name      │
│              (must manually ensure they match indexing config)  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Query RAG System                                        │
│ ───────────────────────                                         │
│ results = retriever.retrieve(                                   │
│     query="your query",      ← User provides                   │
│     k=5                       ← User configurable               │
│ )                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Generate Query Embedding (automatic)                    │
│ ───────────────────────                                         │
│ • Uses retriever's embedder (same as indexing)                 │
│ • Encodes query string into embedding vector                    │
│                                                                 │
│ User configurable: None (uses Retriever's embedder)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: Search Qdrant (automatic)                               │
│ ───────────────────────                                         │
│ • Performs vector similarity search                             │
│ • Uses retriever's qdrant_client                                │
│ • Searches in retriever's collection_name                       │
│ • Returns top k results                                         │
│                                                                 │
│ User configurable:                                              │
│ • k: Number of results to return (default: 5)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Result: List of relevant documents                              │
│ ───────────────────────                                         │
│ [                                                               │
│   {                                                             │
│     "text": "document content...",                              │
│     "score": 0.95,                                              │
│     "metadata": {...}                                           │
│   },                                                            │
│   ...                                                           │
│ ]                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PHASE                               │
└─────────────────────────────────────────────────────────────────┘

1. User creates Indexer
   ├─ Configurable: qdrant_url, collection_name, embedder
   └─ Creates: Embedder, Qdrant connection

2. User calls ingest_file() for each file
   ├─ Configurable: chunk_strategy, chunk_size, overlap, schema
   └─ Processes: Load → Chunk → Index (via indexer)

3. Documents stored in Qdrant
   └─ Same embedder, same collection for all files

┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL PHASE                               │
└─────────────────────────────────────────────────────────────────┘

4. User creates Retriever
   ├─ RECOMMENDED: Pass same indexer (guarantees consistency)
   └─ ALTERNATIVE: Pass embedder + qdrant_url + collection_name
                   (must match indexing configuration)

5. User queries with retriever.retrieve()
   ├─ Configurable: k (number of results)
   └─ Processes: Embed query → Search Qdrant → Return results

6. Results returned
   └─ List of documents with scores and metadata
```

## User-Configurable Parameters Summary

### Indexer Creation

| Parameter         | Type     | Required | Description                                             |
| ----------------- | -------- | -------- | ------------------------------------------------------- |
| `qdrant_url`      | str      | Yes\*    | Qdrant server URL (\*can use env var QDRANT_URL)        |
| `collection_name` | str      | No       | Collection name (default: "artemis_documents")          |
| `embedder`        | Embedder | No       | Embedder instance (default: creates "all-MiniLM-L6-v2") |

### File Ingestion

| Parameter        | Type           | Required | Description                                      |
| ---------------- | -------------- | -------- | ------------------------------------------------ |
| `path`           | str/Path       | Yes      | Path to file                                     |
| `file_type`      | FileType       | Yes      | File type enum (CSV, PDF, DOCX, MD, TEXT)        |
| `indexer`        | Indexer        | Yes      | Indexer instance (reuse same for multiple files) |
| `chunk_strategy` | ChunkStrategy  | No       | Chunking strategy (uses default if None)         |
| `chunk_size`     | int            | No       | Chunk size in characters (strategy-specific)     |
| `overlap`        | int            | No       | Overlap size in characters (for FIXED_OVERLAP)   |
| `schema`         | DocumentSchema | No       | CSV schema (RESTAURANT, TRAVEL) - CSV only       |

### Retriever Creation

| Parameter         | Type          | Required | Description                                            |
| ----------------- | ------------- | -------- | ------------------------------------------------------ |
| `mode`            | RetrievalMode | No       | Search mode (default: SEMANTIC)                        |
| `indexer`         | Indexer       | No\*     | Indexer instance (\*RECOMMENDED - ensures consistency) |
| `embedder`        | Embedder      | No\*     | Embedder instance (\*required if indexer not provided) |
| `qdrant_url`      | str           | No\*     | Qdrant URL (\*required if indexer not provided)        |
| `collection_name` | str           | No       | Collection name (\*required if indexer not provided)   |

### Query Execution

| Parameter | Type | Required | Description                    |
| --------- | ---- | -------- | ------------------------------ |
| `query`   | str  | Yes      | Search query string            |
| `k`       | int  | No       | Number of results (default: 5) |

## Key Design Decisions

### Why Indexer is Required for `ingest_file()`

- **Manages persistent resources**: Qdrant connection, embedder model
- **Resource reuse**: One Indexer can handle multiple files
- **Consistency**: All files use same embedder and collection
- **Separation of concerns**: `ingest_file()` orchestrates, Indexer handles storage

### Why Indexer is Optional (but Recommended) for Retriever

- **Convenience**: Bundles embedder, Qdrant client, collection name
- **Consistency guarantee**: Ensures same embedder/model as indexing
- **Simpler API**: One parameter instead of multiple
- **Flexibility**: Can create Retriever without Indexer (must match config manually)

### Why Same Embedder Must Be Used

- **Vector space consistency**: Different models = different vector spaces
- **Search correctness**: Query embeddings must be in same space as document embeddings
- **Mathematical requirement**: Cosine similarity only works in same vector space

## Common Usage Patterns

### Pattern 1: Single Indexer, Multiple Files (Recommended)

```python
# Create once
indexer = Indexer(collection_name="docs")

# Reuse for multiple files
ingest_file("file1.pdf", FileType.PDF, indexer)
ingest_file("file2.txt", FileType.TEXT, indexer)
ingest_file("file3.csv", FileType.CSV, indexer)

# Share with Retriever
retriever = Retriever(indexer=indexer)
results = retriever.retrieve("query", k=5)
```

### Pattern 2: Custom Chunking Strategy

```python
indexer = Indexer(collection_name="docs")

# Override chunking strategy
ingest_file(
    "document.pdf",
    FileType.PDF,
    indexer,
    chunk_strategy=ChunkStrategy.SEMANTIC,
    chunk_size=1500
)
```

### Pattern 3: Retrieval Without Indexer (Advanced)

```python
# Must ensure embedder and collection match indexing!
embedder = Embedder(model_name="all-MiniLM-L6-v2")  # Must match!
retriever = Retriever(
    embedder=embedder,
    qdrant_url="http://localhost:6333",
    collection_name="docs"  # Must match indexing collection!
)
results = retriever.retrieve("query", k=5)
```

## Notes

- **Always reuse the same Indexer** for multiple files in the same collection
- **Always pass the same Indexer to Retriever** for consistency (recommended)
- **Chunking strategy is per-file** (can use different strategies for different files)
- **Retrieval mode is per-Retriever** (one Retriever = one mode, create multiple for different modes)
- **Number of results (k) is per-query** (can vary per retrieve() call)
