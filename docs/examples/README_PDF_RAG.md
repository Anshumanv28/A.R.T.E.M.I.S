# PDF RAG Integration Guide

This guide shows you how to integrate a PDF file into the A.R.T.E.M.I.S RAG system step-by-step.

## Prerequisites

### 2. Set Up Qdrant

You need a running Qdrant instance. Choose one:

**Option A: Local Qdrant (Docker)**

```bash
docker run -p 6333:6333 qdrant/qdrant
# Then use: QDRANT_URL="http://localhost:6333"
```

**Option B: Qdrant Cloud**

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/)
2. Create a free cluster
3. Copy your cluster URL and API key
4. Set environment variables:
   ```bash
   export QDRANT_URL="your-cluster-url"
   export QDRANT_API_KEY="your-api-key"
   ```

## Quick Start

### Simple Test Script

Use the quick test script for a fast check:

```bash
# 1. Update PDF_PATH in examples/pdf_rag_quick_test.py
# 2. Run the script
python examples/pdf_rag_quick_test.py
```

### Interactive Step-by-Step Guide

For a detailed walkthrough with explanations:

```bash
python examples/pdf_rag_example.py
```

This interactive script will:

- Guide you through each step
- Check prerequisites
- Allow you to test queries interactively

## Manual Integration (Code Example)

Here's how to integrate a PDF manually in your code:

```python
import os
from pathlib import Path
from artemis.rag.core import Indexer, Retriever, RetrievalMode
from artemis.rag.ingestion import ingest_pdf

# Step 1: Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "my_pdf_documents"
PDF_PATH = Path("your_document.pdf")

# Step 2: Create Indexer
# The Indexer manages the embedding model and Qdrant connection
indexer = Indexer(
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    collection_name=COLLECTION_NAME
)

# Step 3: Ingest PDF
# This loads, chunks, and indexes the PDF
ingest_pdf(
    path=PDF_PATH,
    indexer=indexer,
    # Optional: customize chunking
    # chunk_size=1500,
    # overlap=300
)

# Step 4: Create Retriever
# Use the same Indexer to ensure consistency
retriever = Retriever(
    mode=RetrievalMode.SEMANTIC,
    indexer=indexer  # Recommended: pass indexer
)

# Step 5: Query the RAG System
results = retriever.retrieve("What is the main topic?", k=5)

for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Text: {result['text'][:200]}...")
    print()
```

## Understanding the Steps

### Step 1: Create Indexer

The `Indexer` is a manager class that:

- Loads the embedding model (default: `all-MiniLM-L6-v2`)
- Connects to Qdrant
- Creates/verifies the collection exists
- Handles document storage

**Why create it once?**

- Reuse the same embedding model across multiple files
- Share Qdrant connection (efficient)
- Store all files in the same collection

### Step 2: Ingest PDF

The `ingest_pdf()` function handles the full pipeline:

1. **Load**: Extracts text from PDF using `pdfplumber` or `PyPDF2`
2. **Chunk**: Splits text into chunks (default: fixed-size chunks)
3. **Index**: Generates embeddings and stores in Qdrant

**Customization options:**

```python
from artemis.rag.ingestion import ChunkStrategy

ingest_pdf(
    path=PDF_PATH,
    indexer=indexer,
    chunk_strategy=ChunkStrategy.SEMANTIC,  # Use semantic chunking
    chunk_size=1500,                        # Chunk size in characters
    overlap=300                            # Overlap between chunks
)
```

### Step 3: Create Retriever

The `Retriever` performs semantic search. **Always use the same Indexer** to ensure:

- Same embedding model (critical!)
- Same Qdrant connection
- Same collection

### Step 4: Query

The `retrieve()` method:

1. Embeds your query using the same model
2. Searches for similar chunks in Qdrant
3. Returns top-k most relevant results

## Chunking Strategies

You can customize how PDFs are chunked:

- **FIXED** (default): Fixed-size chunks with optional overlap
- **SEMANTIC**: Chunks based on semantic boundaries
- **AGENTIC**: AI-powered intelligent chunking

Example:

```python
from artemis.rag.ingestion import ChunkStrategy

ingest_pdf(
    path=PDF_PATH,
    indexer=indexer,
    chunk_strategy=ChunkStrategy.SEMANTIC
)
```

## Retrieval Modes

The system supports different retrieval modes:

- **SEMANTIC** (default): Vector similarity search
- **KEYWORD**: BM25/TF-IDF based search
- **HYBRID**: Combines semantic and keyword search

Example:

```python
retriever = Retriever(
    mode=RetrievalMode.HYBRID,
    indexer=indexer
)
```

## Troubleshooting

### "PDF file not found"

- Check the file path is correct
- Use absolute path if relative path doesn't work

### "No PDF libraries found"

- Install `pdfplumber` or `PyPDF2`:
  ```bash
  pip install pdfplumber
  ```

### "Failed to connect to Qdrant"

- Make sure Qdrant is running
- Check `QDRANT_URL` environment variable
- For local Qdrant: `docker run -p 6333:6333 qdrant/qdrant`

### "No results found"

- Make sure PDF was ingested successfully
- Try a different query
- Check collection has documents: `collection_info.points_count`

### "Import errors"

- Make sure you're in the project root or have installed the package
- Try: `pip install -e .` from project root

## Next Steps

- **Add more PDFs**: Use the same Indexer to add multiple PDFs
- **Experiment with chunking**: Try different strategies and parameters
- **Try different retrieval modes**: Test HYBRID or KEYWORD modes
- **Add metadata**: Customize metadata extraction for better filtering

## Example Workflow

```python
# 1. Create Indexer once
indexer = Indexer(collection_name="my_docs")

# 2. Ingest multiple PDFs
ingest_pdf("document1.pdf", indexer)
ingest_pdf("document2.pdf", indexer)
ingest_pdf("document3.pdf", indexer)

# 3. Create Retriever
retriever = Retriever(indexer=indexer)

# 4. Query across all PDFs
results = retriever.retrieve("your question", k=5)
```

All PDFs are stored in the same collection and can be searched together!
