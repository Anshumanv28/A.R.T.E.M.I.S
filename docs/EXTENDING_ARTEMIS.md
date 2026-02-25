# Extending A.R.T.E.M.I.S.

This guide shows you how to extend A.R.T.E.M.I.S. with custom components. A.R.T.E.M.I.S. uses a registry pattern that makes it easy to add new functionality without modifying core code.

## Table of Contents

1. [Custom CSV Schema Converters](#custom-csv-schema-converters)
2. [Custom Chunking Strategies](#custom-chunking-strategies)
3. [Custom Retrieval Strategies](#custom-retrieval-strategies)
4. [Custom Metadata Extractors](#custom-metadata-extractors)
5. [Custom Loaders](#custom-loaders)
6. [Registration Patterns](#registration-patterns)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Custom CSV Schema Converters

CSV schema converters transform structured CSV data into formatted text documents optimized for semantic search.

### Quick Start

1. Create a new file: `my_project/my_schema.py`
2. Use the template below
3. Import it in your code before using

### Template

```python
"""
Custom CSV schema converter for [Your Domain].

Expected CSV columns: [list columns]
"""

import pandas as pd
from typing import List, Dict, Tuple
from artemis.rag.ingestion.converters.csv_converter import (
    register_csv_schema,
    format_doc,
    DocumentSchema
)
from artemis.utils import get_logger

logger = get_logger(__name__)

# Option 1: Use existing schema enum value
SCHEMA = DocumentSchema.SUPPORT  # or DocumentSchema.RESTAURANT, DocumentSchema.TRAVEL

# Option 2: Create custom schema (if not in enum)
# SCHEMA = DocumentSchema("my_custom_schema")

@register_csv_schema(SCHEMA)
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Convert CSV to formatted documents.

    Args:
        csv_path: Path to CSV file

    Returns:
        Tuple of (documents, metadata_list)
    """
    df = pd.read_csv(csv_path)
    documents = []
    metadata_list = []

    for idx, row in df.iterrows():
        # Extract and format fields
        field1 = str(row.get("column1", "")).strip()
        field2 = str(row.get("column2", "")).strip()

        # Build document using format_doc helper
        doc_parts = {
            "Field 1": field1,
            "Field 2": field2,
            # Add more fields...
        }

        document_text = format_doc(doc_parts)
        documents.append(document_text)

        # Store metadata for filtering
        metadata = {
            "column1": field1,
            "column2": field2,
            # Add more metadata...
        }
        metadata_list.append(metadata)

    logger.info(f"Converted {len(documents)} documents")
    return documents, metadata_list

# Usage:
# from my_project.my_schema import convert_my_schema, SCHEMA
# from artemis.rag import ingest_file, FileType, Indexer
#
# indexer = Indexer()
# ingest_file("data.csv", FileType.CSV, indexer, schema=SCHEMA)
```

### Function Signature

```python
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Args:
        csv_path: Path to CSV file (str or Path)

    Returns:
        Tuple of:
        - documents: List[str] - Formatted text documents (one per row)
        - metadata_list: List[Dict] - Metadata dictionaries (one per row)
    """
```

### Best Practices

- **Use `format_doc()`**: Ensures consistent document formatting across converters
- **Include all relevant fields in metadata**: Enables filtering during retrieval
- **Handle missing/null values gracefully**: Use `pd.notna()` checks
- **Log conversion progress**: Use the logger for debugging
- **Validate input**: Check for required columns before processing

### Example: Restaurant Converter

See `artemis/rag/ingestion/converters/schemas/restaurant.py` for a complete implementation.

---

## Custom Chunking Strategies

Chunking strategies split content into smaller pieces suitable for embedding and retrieval.

### Quick Start

1. Create a new file: `my_project/my_chunker.py`
2. Use the template below
3. Import it before using `ingest_file()`

### Template

```python
"""
Custom chunking strategy for [Your Use Case].
"""

from typing import List, Dict, Tuple, Any
from artemis.rag.ingestion.chunkers.registry import (
    register_chunker,
    ChunkStrategy
)
from artemis.utils import get_logger

logger = get_logger(__name__)

# Create or use existing strategy
STRATEGY = ChunkStrategy("my_custom_chunker")

@register_chunker(STRATEGY)
def my_custom_chunker(
    content: Any,  # DataFrame for CSV, str for text files
    **kwargs
) -> Tuple[List[str], List[Dict]]:
    """
    Custom chunking logic.

    Args:
        content: Input content (DataFrame for CSV, str for text)
        **kwargs: Additional parameters (chunk_size, overlap, etc.)

    Returns:
        Tuple of (documents, metadata_list)
    """
    documents = []
    metadata_list = []

    # Your chunking logic here
    # For text files:
    if isinstance(content, str):
        # Split text into chunks
        chunk_size = kwargs.get("chunk_size", 800)
        overlap = kwargs.get("overlap", 200)

        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - overlap  # Apply overlap

        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadata_list.append({
                "chunk_index": i,
                "source_type": "text",
                "chunk_size": len(chunk)
            })

    # For CSV files:
    elif hasattr(content, 'iterrows'):  # DataFrame
        # Process rows
        for idx, row in content.iterrows():
            # Your row processing logic
            doc_text = format_row_as_document(row)
            documents.append(doc_text)
            metadata_list.append({
                "row_index": idx,
                "source_type": "csv"
            })

    logger.info(f"Created {len(documents)} chunks")
    return documents, metadata_list

# Usage:
# from my_project.my_chunker import STRATEGY
# from artemis.rag import ingest_file, FileType, Indexer
#
# indexer = Indexer()
# ingest_file("file.pdf", FileType.PDF, indexer, chunk_strategy=STRATEGY)
```

### Function Signature

```python
def my_chunker(content: Any, **kwargs) -> Tuple[List[str], List[Dict]]:
    """
    Args:
        content:
            - DataFrame for CSV files
            - str for text files (PDF, DOCX, MD, TEXT)
        **kwargs: Strategy-specific parameters
            - chunk_size: int (for fixed-size chunkers)
            - overlap: int (for overlap chunkers)
            - schema: DocumentSchema (for CSV chunkers)

    Returns:
        Tuple of:
        - documents: List[str] - Chunked text documents
        - metadata_list: List[Dict] - Metadata for each chunk
    """
```

### Available Strategies

- `ChunkStrategy.CSV_ROW` - Row-based chunking for CSV files
- `ChunkStrategy.FIXED` - Fixed-size chunks without overlap
- `ChunkStrategy.FIXED_OVERLAP` - Fixed-size chunks with overlap
- `ChunkStrategy.SEMANTIC` - Sentence/paragraph-aware chunking
- `ChunkStrategy.AGENTIC` - LLM-driven chunking

### Example: Fixed Overlap Chunker

See `artemis/rag/ingestion/chunkers/fixed_chunker.py` for a complete implementation.

---

## Custom Retrieval Strategies

Retrieval strategies implement different search methods (semantic, keyword, hybrid, etc.).

### Quick Start

1. Create a new file: `artemis/rag/strategies/my_strategy.py` (or your own module)
2. Use the template below
3. Import it in `artemis/rag/strategies/__init__.py` (if in artemis) or import in your code

### Template

```python
"""
Custom retrieval strategy for [Your Search Method].
"""

from typing import List, Dict, Any
from artemis.rag.core.retriever import (
    register_strategy,
    RetrievalMode,
    Retriever
)
from artemis.utils import get_logger

logger = get_logger(__name__)

# Option 1: Use existing mode
# MODE = RetrievalMode.SEMANTIC

# Option 2: Create new mode (add to RetrievalMode enum first)
# MODE = RetrievalMode("my_custom_mode")

@register_strategy(RetrievalMode.SEMANTIC)  # or your custom mode
def my_custom_search(
    retriever: Retriever,
    query: str,
    k: int = 5,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Custom search implementation.

    Args:
        retriever: Retriever instance (provides qdrant_client, collection_name, etc.)
        query: Search query string
        k: Number of results to return
        **kwargs: Additional search parameters

    Returns:
        List of dictionaries with 'text', 'score', and 'metadata' keys
    """
    # Access retriever resources
    qdrant_client = retriever.qdrant_client
    collection_name = retriever.collection_name
    embedder = retriever.embedder

    # Your search logic here
    # Example: Custom vector search
    query_vector = embedder.embed([query])[0]

    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=k,
        **kwargs
    )

    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "text": result.payload.get("text", ""),
            "score": result.score,
            "metadata": result.payload.get("metadata", {})
        })

    return formatted_results

# Usage:
# from artemis.rag import Retriever, RetrievalMode
#
# retriever = Retriever(mode=RetrievalMode.SEMANTIC)
# results = retriever.retrieve("your query", k=5)
```

### Function Signature

```python
def my_search(
    retriever: Retriever,
    query: str,
    k: int = 5,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Args:
        retriever: Retriever instance with:
            - qdrant_client: QdrantClient instance
            - collection_name: str
            - embedder: Embedder instance
        query: Search query string
        k: Number of results to return
        **kwargs: Strategy-specific parameters

    Returns:
        List of dictionaries, each with:
        - text: str - Document text
        - score: float - Relevance score
        - metadata: Dict - Document metadata
    """
```

### Available Modes

- `RetrievalMode.SEMANTIC` - Semantic vector search (default)
- `RetrievalMode.KEYWORD` - Keyword-based search (BM25/TF-IDF)
- `RetrievalMode.HYBRID` - Combined semantic + keyword search

### Example: Semantic Search Strategy

See `artemis/rag/strategies/semantic.py` for a complete implementation.

---

## Custom Metadata Extractors

Metadata extractors extract structured metadata from content for each chunk.

### Template

```python
"""
Custom metadata extractor for [File Type].
"""

from typing import List, Dict, Any
from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)

class MyMetadataExtractor(MetadataExtractor):
    """Extract metadata from [file type]."""

    def extract(self, content: Any, **kwargs) -> List[Dict]:
        """
        Extract metadata for each chunk.

        Args:
            content: File content (type depends on file type)
            **kwargs: Additional extraction parameters

        Returns:
            List of metadata dictionaries (one per chunk)
        """
        metadata_list = []

        # Your extraction logic here
        # Map chunks to metadata (page numbers, sections, etc.)

        # Example: Extract page numbers for PDF
        if "page_numbers" in kwargs:
            page_numbers = kwargs["page_numbers"]
            for i, page_num in enumerate(page_numbers):
                metadata_list.append({
                    "page_number": page_num,
                    "chunk_index": i,
                    "source_type": "pdf"
                })

        return metadata_list
```

### Base Class

```python
from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor

class MyExtractor(MetadataExtractor):
    def extract(self, content: Any, **kwargs) -> List[Dict]:
        # Implementation
        pass
```

### Example: CSV Metadata Extractor

See `artemis/rag/ingestion/metadata_extractors/csv_extractor.py` for a complete implementation.

---

## Custom Loaders

Loaders extract raw content from files (format-specific file reading).

### Template

```python
"""
Custom loader for [File Type].
"""

from pathlib import Path
from typing import Union

def load_my_format(path: Union[str, Path]) -> Any:
    """
    Load content from [file type] file.

    Args:
        path: Path to file

    Returns:
        Raw content (DataFrame for CSV, str for text, etc.)
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Your loading logic here
    # For text files, return str
    # For CSV files, return pandas.DataFrame
    # etc.

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    return content
```

### Available Loaders

- `load_csv(path)` → `pandas.DataFrame`
- `load_pdf_text(path)` → `str`
- `load_docx_text(path)` → `str`
- `load_md_text(path)` → `str`
- `load_text(path)` → `str`

### Example: PDF Loader

See `artemis/rag/ingestion/loaders/pdf_loader.py` for a complete implementation.

---

## Registration Patterns

### Pattern 1: CSV Schema Converter

```python
from artemis.rag.ingestion.converters.csv_converter import (
    register_csv_schema,
    DocumentSchema
)

@register_csv_schema(DocumentSchema.MY_SCHEMA)
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    # Implementation
    return documents, metadata
```

### Pattern 2: Chunking Strategy

```python
from artemis.rag.ingestion.chunkers.registry import (
    register_chunker,
    ChunkStrategy
)

@register_chunker(ChunkStrategy("my_chunker"))
def my_chunker(content: Any, **kwargs) -> Tuple[List[str], List[Dict]]:
    # Implementation
    return documents, metadata
```

### Pattern 3: Retrieval Strategy

```python
from artemis.rag.core.retriever import (
    register_strategy,
    RetrievalMode
)

@register_strategy(RetrievalMode.MY_MODE)
def my_search(retriever: Retriever, query: str, k: int) -> List[Dict]:
    # Implementation
    return results
```

### Auto-Registration

Components are automatically registered when their module is imported:

```python
# In your main code:
from my_project import my_schema  # Registers converter
from my_project import my_chunker  # Registers chunker
from my_project import my_strategy  # Registers strategy

# Now use them:
from artemis.rag import ingest_file, FileType, Indexer

indexer = Indexer()
ingest_file("data.csv", FileType.CSV, indexer, schema=DocumentSchema.MY_SCHEMA)
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
try:
    df = pd.read_csv(csv_path)
except Exception as e:
    logger.exception(f"Failed to load CSV: {csv_path}")
    raise
```

### 2. Logging

Use the logger for debugging:

```python
from artemis.utils import get_logger

logger = get_logger(__name__)
logger.info(f"Processing {len(documents)} documents")
logger.debug(f"Chunk size: {chunk_size}")
```

### 3. Type Hints

Always include type hints:

```python
from typing import List, Dict, Tuple

def my_function(csv_path: str) -> Tuple[List[str], List[Dict]]:
    # Implementation
    pass
```

### 4. Documentation

Document your functions:

```python
def my_function(param: str) -> List[str]:
    """
    Brief description.

    Args:
        param: Parameter description

    Returns:
        Return value description
    """
    pass
```

### 5. Testing

Test your custom components:

```python
def test_my_converter():
    docs, metadata = convert_my_schema("test_data.csv")
    assert len(docs) > 0
    assert len(metadata) == len(docs)
```

---

## Troubleshooting

### Component Not Registered

**Problem**: Your custom component isn't being recognized.

**Solution**:

- Ensure the module is imported before use
- Check that the decorator is applied correctly
- Verify the import path is correct

```python
# Import before use
from my_project import my_schema  # This registers it

# Now use it
from artemis.rag import ingest_file, FileType
ingest_file("data.csv", FileType.CSV, indexer, schema=DocumentSchema.MY_SCHEMA)
```

### Import Errors

**Problem**: Import errors when using custom components.

**Solution**:

- Check that all dependencies are installed
- Verify import paths are correct
- Ensure the component file is in the Python path

### Type Errors

**Problem**: Type errors with function signatures.

**Solution**:

- Verify function signature matches expected pattern
- Check return types match `Tuple[List[str], List[Dict]]`
- Ensure all required parameters are present

### Registration Conflicts

**Problem**: Multiple components registered for the same strategy/mode.

**Solution**:

- The last registered component wins
- Use unique strategy/mode names
- Check for duplicate registrations

---

## Getting Help

- Check existing implementations in:
  - `artemis/rag/ingestion/converters/schemas/` for CSV converters
  - `artemis/rag/ingestion/chunkers/` for chunkers
  - `artemis/rag/strategies/` for retrieval strategies
- See examples in `examples/` directory
- Review [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common patterns
- Review README.md for API documentation

---

## Registration Checklist

When creating a new component:

- [ ] Component follows the expected interface/signature
- [ ] Component is registered using the appropriate decorator
- [ ] Component is imported before use (for auto-registration)
- [ ] Component includes proper logging
- [ ] Component handles errors gracefully
- [ ] Component is documented with docstrings
- [ ] Component includes type hints
- [ ] Component is tested (if applicable)
