# A.R.T.E.M.I.S. Quick Reference

Quick reference cheat sheet for extending A.R.T.E.M.I.S.

## Registration Decorators

| Component          | Decorator              | Location                                         | Example                                           |
| ------------------ | ---------------------- | ------------------------------------------------ | ------------------------------------------------- |
| CSV Schema         | `@register_csv_schema` | `artemis.rag.ingestion.converters.csv_converter` | `@register_csv_schema(DocumentSchema.RESTAURANT)` |
| Chunker            | `@register_chunker`    | `artemis.rag.ingestion.chunkers.registry`        | `@register_chunker(ChunkStrategy.SEMANTIC)`       |
| Retrieval Strategy | `@register_strategy`   | `artemis.rag.core.retriever`                     | `@register_strategy(RetrievalMode.SEMANTIC)`      |

## Function Signatures

### CSV Schema Converter

```python
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Args:
        csv_path: Path to CSV file

    Returns:
        Tuple of (documents, metadata_list)
    """
```

### Chunker

```python
def my_chunker(content: Any, **kwargs) -> Tuple[List[str], List[Dict]]:
    """
    Args:
        content: DataFrame for CSV, str for text files
        **kwargs: chunk_size, overlap, schema, etc.

    Returns:
        Tuple of (documents, metadata_list)
    """
```

### Retrieval Strategy

```python
def my_search(
    retriever: Retriever,
    query: str,
    k: int = 5,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Args:
        retriever: Retriever instance
        query: Search query string
        k: Number of results

    Returns:
        List[{"text": str, "score": float, "metadata": dict}]
    """
```

## Import Paths

### CSV Schemas

```python
from artemis.rag.ingestion.converters.csv_converter import (
    register_csv_schema,
    DocumentSchema,
    format_doc,
    CSV_CONVERTERS
)
```

### Chunkers

```python
from artemis.rag.ingestion.chunkers.registry import (
    register_chunker,
    ChunkStrategy,
    CHUNKERS,
    FileType,
    DEFAULT_CHUNK_FOR_FILETYPE
)
```

### Retrieval Strategies

```python
from artemis.rag.core.retriever import (
    register_strategy,
    RetrievalMode,
    Retriever,
    RETRIEVAL_STRATEGIES
)
```

### Metadata Extractors

```python
from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
```

## Common Code Snippets

### Register CSV Schema

```python
from artemis.rag.ingestion.converters.csv_converter import (
    register_csv_schema,
    DocumentSchema,
    format_doc
)
import pandas as pd

@register_csv_schema(DocumentSchema.MY_SCHEMA)
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    df = pd.read_csv(csv_path)
    documents = []
    metadata_list = []

    for idx, row in df.iterrows():
        doc_parts = {"Field": str(row.get("column", ""))}
        documents.append(format_doc(doc_parts))
        metadata_list.append({"column": row.get("column")})

    return documents, metadata_list
```

### Register Chunker

```python
from artemis.rag.ingestion.chunkers.registry import (
    register_chunker,
    ChunkStrategy
)

@register_chunker(ChunkStrategy("my_chunker"))
def my_chunker(content: Any, **kwargs) -> Tuple[List[str], List[Dict]]:
    chunk_size = kwargs.get("chunk_size", 800)
    documents = []
    metadata_list = []

    if isinstance(content, str):
        # Text chunking logic
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            documents.append(chunk)
            metadata_list.append({"chunk_index": i})

    return documents, metadata_list
```

### Register Retrieval Strategy

```python
from artemis.rag.core.retriever import (
    register_strategy,
    RetrievalMode,
    Retriever
)

@register_strategy(RetrievalMode.SEMANTIC)
def my_search(
    retriever: Retriever,
    query: str,
    k: int = 5
) -> List[Dict[str, Any]]:
    query_vector = retriever.embedder.embed([query])[0]

    results = retriever.qdrant_client.search(
        collection_name=retriever.collection_name,
        query_vector=query_vector,
        limit=k
    )

    return [
        {
            "text": r.payload.get("text", ""),
            "score": r.score,
            "metadata": r.payload.get("metadata", {})
        }
        for r in results
    ]
```

## Enums

### DocumentSchema

```python
from artemis.rag.ingestion.converters.csv_converter import DocumentSchema

DocumentSchema.RESTAURANT
DocumentSchema.TRAVEL
DocumentSchema.SUPPORT
# Or create custom: DocumentSchema("my_schema")
```

### ChunkStrategy

```python
from artemis.rag.ingestion.chunkers.registry import ChunkStrategy

ChunkStrategy.CSV_ROW
ChunkStrategy.FIXED
ChunkStrategy.FIXED_OVERLAP
ChunkStrategy.SEMANTIC
ChunkStrategy.AGENTIC
# Or create custom: ChunkStrategy("my_chunker")
```

### RetrievalMode

```python
from artemis.rag.core.retriever import RetrievalMode

RetrievalMode.SEMANTIC
RetrievalMode.KEYWORD
RetrievalMode.HYBRID
# Or create custom: RetrievalMode("my_mode")
```

### FileType

```python
from artemis.rag.ingestion.chunkers.registry import FileType

FileType.CSV
FileType.PDF
FileType.DOCX
FileType.MD
FileType.TEXT
```

## Usage Patterns

### Using Custom CSV Schema

```python
# Import to register
from my_project import my_schema

# Use it
from artemis.rag import ingest_file, FileType, Indexer, DocumentSchema

indexer = Indexer()
ingest_file("data.csv", FileType.CSV, indexer, schema=DocumentSchema.MY_SCHEMA)
```

### Using Custom Chunker

```python
# Import to register
from my_project import my_chunker

# Use it
from artemis.rag import ingest_file, FileType, Indexer, ChunkStrategy

indexer = Indexer()
ingest_file("file.pdf", FileType.PDF, indexer, chunk_strategy=ChunkStrategy("my_chunker"))
```

### Using Custom Retrieval Strategy

```python
# Import to register
from my_project import my_strategy

# Use it
from artemis.rag import Retriever, RetrievalMode

retriever = Retriever(mode=RetrievalMode.MY_MODE)
results = retriever.retrieve("query", k=5)
```

## Helper Functions

### format_doc()

```python
from artemis.rag.ingestion.converters.csv_converter import format_doc

doc_parts = {
    "Field1": "value1",
    "Field2": "value2"
}

document = format_doc(doc_parts)
# Returns: "Field1: value1. Field2: value2."
```

### get_logger()

```python
from artemis.utils import get_logger

logger = get_logger(__name__)
logger.info("Processing documents")
logger.debug(f"Chunk size: {chunk_size}")
logger.warning("Low chunk count")
logger.error("Failed to process")
```

## Registry Access

### Check Registered Components

```python
# CSV Converters
from artemis.rag.ingestion.converters.csv_converter import CSV_CONVERTERS
print(CSV_CONVERTERS.keys())  # {DocumentSchema.RESTAURANT, ...}

# Chunkers
from artemis.rag.ingestion.chunkers.registry import CHUNKERS
print(CHUNKERS.keys())  # {ChunkStrategy.SEMANTIC, ...}

# Retrieval Strategies
from artemis.rag.core.retriever import RETRIEVAL_STRATEGIES
print(RETRIEVAL_STRATEGIES.keys())  # {RetrievalMode.SEMANTIC, ...}
```

## Default Mappings

### Default Chunking Strategy by File Type

```python
from artemis.rag.ingestion.chunkers.registry import DEFAULT_CHUNK_FOR_FILETYPE

DEFAULT_CHUNK_FOR_FILETYPE = {
    FileType.CSV: ChunkStrategy.CSV_ROW,
    FileType.PDF: ChunkStrategy.FIXED_OVERLAP,
    FileType.DOCX: ChunkStrategy.FIXED_OVERLAP,
    FileType.MD: ChunkStrategy.SEMANTIC,
    FileType.TEXT: ChunkStrategy.FIXED_OVERLAP,
}
```

## Common Patterns

### Pattern 1: CSV Schema Converter

```python
@register_csv_schema(DocumentSchema.MY_SCHEMA)
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    # Implementation
```

### Pattern 2: Chunking Strategy

```python
@register_chunker(ChunkStrategy("my_chunker"))
def my_chunker(content: Any, **kwargs) -> Tuple[List[str], List[Dict]]:
    # Implementation
```

### Pattern 3: Retrieval Strategy

```python
@register_strategy(RetrievalMode.MY_MODE)
def my_search(retriever: Retriever, query: str, k: int) -> List[Dict]:
    # Implementation
```

## File Locations

### Core Components

- `artemis/rag/core/embedder.py` - Embedding generation
- `artemis/rag/core/indexer.py` - Document indexing
- `artemis/rag/core/retriever.py` - Document retrieval

### Ingestion Components

- `artemis/rag/ingestion/ingestion.py` - Main ingestion orchestrator
- `artemis/rag/ingestion/converters/` - CSV converters
- `artemis/rag/ingestion/converters/schemas/` - CSV schema converters
- `artemis/rag/ingestion/chunkers/` - Chunking strategies
- `artemis/rag/ingestion/loaders/` - File loaders
- `artemis/rag/ingestion/metadata_extractors/` - Metadata extractors

### Retrieval Components

- `artemis/rag/strategies/` - Retrieval strategies

## See Also

- [EXTENDING_ARTEMIS.md](EXTENDING_ARTEMIS.md) - Comprehensive developer guide
- [README.md](../README.md) - Main documentation
- `examples/templates/` - Template files for common patterns
