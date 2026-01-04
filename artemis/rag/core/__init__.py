"""
Core RAG components for A.R.T.E.M.I.S.

This module contains the core functionality for document conversion,
ingestion, and retrieval.
"""

# Import document converter (no external dependencies)
from artemis.rag.core.document_converter import (
    csv_to_documents,
    DocumentSchema,
    register_schema,
    format_doc,
)

# Import embedder (requires sentence_transformers - optional)
try:
    from artemis.rag.core.embedder import Embedder
    _EMBEDDER_AVAILABLE = True
except ImportError:
    # Embedder not available if sentence_transformers is not installed
    Embedder = None
    _EMBEDDER_AVAILABLE = False

# Import chunking components (no external dependencies)
try:
    from artemis.rag.core.chunker import (
        FileType,
        ChunkStrategy,
        register_chunker,
        DEFAULT_CHUNK_FOR_FILETYPE,
    )
    from artemis.rag.core.ingestion import (
        ingest_file,
        ingest_csv,
        ingest_pdf,
        ingest_docx,
        ingest_md,
        ingest_text,
    )
    # Auto-register chunkers
    try:
        from artemis.rag.core import chunkers  # noqa: F401
    except ImportError:
        pass
    _CHUNKING_AVAILABLE = True
except ImportError:
    FileType = None
    ChunkStrategy = None
    register_chunker = None
    DEFAULT_CHUNK_FOR_FILETYPE = None
    ingest_file = None
    ingest_csv = None
    ingest_pdf = None
    ingest_docx = None
    ingest_md = None
    ingest_text = None
    _CHUNKING_AVAILABLE = False

# Import retriever and indexer (requires qdrant_client - optional)
try:
    from artemis.rag.core.retriever import Retriever, RetrievalMode, register_strategy
    from artemis.rag.core.indexer import Indexer
    _RETRIEVER_AVAILABLE = True
except ImportError:
    # Retriever/Indexer not available if qdrant_client is not installed
    Retriever = None
    RetrievalMode = None
    register_strategy = None
    Indexer = None
    _RETRIEVER_AVAILABLE = False

__all__ = [
    "csv_to_documents",
    "DocumentSchema",
    "register_schema",
    "format_doc",
]

# Add embedder to exports if available
if _EMBEDDER_AVAILABLE:
    __all__.append("Embedder")

# Add chunking components to exports if available
if _CHUNKING_AVAILABLE:
    __all__.extend([
        "FileType",
        "ChunkStrategy",
        "register_chunker",
        "DEFAULT_CHUNK_FOR_FILETYPE",
        "ingest_file",
        "ingest_csv",
        "ingest_pdf",
        "ingest_docx",
        "ingest_md",
        "ingest_text",
    ])

# Add retriever and indexer to exports if available
if _RETRIEVER_AVAILABLE:
    __all__.extend(["Retriever", "RetrievalMode", "Indexer", "register_strategy"])

