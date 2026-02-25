# Hybrid Search Implementation & Fixes

## Overview

This document summarizes the implementation of hybrid search (semantic + keyword) and related fixes to the A.R.T.E.M.I.S. RAG system.

## Changes Made

### 1. Hybrid Search Implementation (Keyword + Semantic)

**Date:** January 2025

**What:** Implemented hybrid search strategy that combines semantic vector search (70% weight) with BM25 keyword search (30% weight).

**Files Modified:**

- `artemis/rag/strategies/keyword.py` - Implemented BM25 keyword search
- `artemis/rag/strategies/hybrid.py` - Implemented hybrid search combining both strategies

**Key Features:**

- **Keyword Search (BM25):** Fetches all documents from Qdrant, builds BM25 index, scores queries for exact term matching
- **Hybrid Search:** Combines normalized semantic and keyword scores with configurable weights (default: 70% semantic, 30% keyword)
- **Caching:** BM25 indexes are cached per collection to avoid rebuilding on every query
- **Fallback:** If one search method fails, falls back to the other

**Usage:**

```python
from artemis.rag.core import Retriever, RetrievalMode, Indexer

indexer = Indexer(collection_name="my_docs")
retriever = Retriever(mode=RetrievalMode.HYBRID, indexer=indexer)
results = retriever.retrieve("your query", k=5)
```

**Dependencies:**

- `rank-bm25` package (install with: `pip install rank-bm25`)

---

### 2. Collection Name Fix

**Date:** January 2025

**Problem:** Retriever was not correctly using the collection name from the Indexer, causing queries to fail or query wrong collections.

**Root Cause:** When an Indexer was provided, the Retriever should use `indexer.collection_name` but was defaulting to `"artemis_documents"` in some cases.

**Fix:**

- Modified `artemis/rag/core/retriever.py` to explicitly set `self.collection_name = indexer.collection_name` when an Indexer is provided
- Added validation to ensure `collection_name` is always set
- Added collection existence check before querying

**Files Modified:**

- `artemis/rag/core/retriever.py`

**Key Changes:**

```python
# Before: Could default to wrong collection
# After: Explicitly uses indexer.collection_name
if indexer is not None:
    self.collection_name = indexer.collection_name  # Explicit assignment
    # ... validation and existence checks
```

**Impact:**

- Fixes collection mismatch errors
- Ensures queries target the correct collection
- Works correctly for both CSV data (large collections) and document collections

---

### 3. Validation & Error Handling Improvements

**Date:** January 2025

**What:** Added comprehensive validation and better error messages.

**Changes:**

1. **Collection Name Validation:**

   - Validates `collection_name` is set before querying
   - Checks if Indexer has valid `collection_name` attribute
   - Raises clear error if collection_name is missing

2. **Collection Existence Check:**

   - Verifies collection exists in Qdrant before querying
   - Provides helpful error message with available collections if not found
   - Logs collection point count for debugging

3. **Better Error Messages:**
   - Clear error messages for missing collections
   - Validation errors explain what's wrong and how to fix it

**Files Modified:**

- `artemis/rag/core/retriever.py`

---

## Agent/LLM Integration

### How Agents Interact with RAG

Agents and LLMs interact with the RAG system **exactly like humans do** - by generating queries:

1. **Agent generates a query** (e.g., "What are the pricing tiers?")
2. **Query is sent to Retriever** via `retriever.retrieve(query, k=5)`
3. **Retriever returns relevant chunks** with scores and metadata
4. **Agent/LLM uses chunks** to generate a response

### Query Types Supported

**Any natural language query works**, but the system handles:

- **Semantic queries:** "What is the remote work policy?" (understands meaning)
- **Keyword queries:** "Q3 success criteria" (exact term matching via BM25)
- **Hybrid queries:** "pricing tiers for CloudSync Pro" (benefits from both)
- **Filtered queries:** "restaurants with rating above 4 in Noida" (metadata filtering)

### Best Practices for Agents

1. **Use natural language:** Agents can generate queries naturally - no special format needed
2. **Be specific:** More specific queries (e.g., "Q3 2024 planning meeting notes") work better than vague ones
3. **Leverage metadata:** For structured data, include filter conditions in queries (e.g., "restaurants in Mumbai with online delivery")
4. **Hybrid search recommended:** Use `RetrievalMode.HYBRID` for best results (combines semantic understanding + exact matching)

### Example Agent Integration

```python
from artemis.rag.core import Retriever, RetrievalMode, Indexer

# Setup (once)
indexer = Indexer(collection_name="knowledge_base")
retriever = Retriever(mode=RetrievalMode.HYBRID, indexer=indexer)

# Agent query generation (in your agent loop)
def agent_query(user_question: str) -> str:
    # Agent generates query (could be same as user_question or reformulated)
    query = user_question  # or agent.reformulate(user_question)

    # Retrieve relevant chunks
    results = retriever.retrieve(query, k=5)

    # Build context from results
    context = "\n\n".join([r['text'] for r in results])

    # Generate response using context
    response = llm.generate(f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:")
    return response
```

---

## Testing

### Verified Working:

- ✅ Hybrid search on techcorp_docs (small collection)
- ✅ Collection name inheritance from Indexer
- ✅ Query results are relevant and properly scored
- ✅ Metadata filtering (for CSV data)
- ✅ Interactive query mode

### Known Limitations:

- ⚠️ Large collections (9000+ documents) with complex filters may timeout
  - **Workaround:** Use simpler queries or increase Qdrant timeout
- ⚠️ BM25 index building requires fetching all documents (first query is slower)

---

## Migration Notes

### For Existing Code:

**Before:**

```python
retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
```

**After (recommended):**

```python
retriever = Retriever(mode=RetrievalMode.HYBRID, indexer=indexer)
```

**No other changes required** - hybrid search is a drop-in replacement that provides better results.

---

## Summary

- **Hybrid search:** Implemented and working (semantic + keyword)
- **Collection name fix:** Resolved collection mismatch issues
- **Validation:** Added comprehensive checks and error handling
- **Agent integration:** Agents use queries just like humans - any natural language query works
