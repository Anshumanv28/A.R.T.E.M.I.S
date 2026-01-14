"""
RAG (Retrieval Augmented Generation) module for A.R.T.E.M.I.S.

This module provides a clean interface to all RAG functionality:
- Document indexing (core/indexer.py)
- Document retrieval (core/retriever.py)
- File ingestion with chunking (ingestion/)
- CSV schema converters (ingestion/converters/schemas/)
- Retrieval strategies (strategies/)
"""

# Import core RAG components
try:
    from artemis.rag.core import Retriever, RetrievalMode, register_strategy, Indexer
    _RETRIEVER_AVAILABLE = True
except ImportError:
    # Retriever/Indexer not available if qdrant_client is not installed
    Retriever = None
    RetrievalMode = None
    register_strategy = None
    Indexer = None
    _RETRIEVER_AVAILABLE = False

# Import ingestion components
try:
    from artemis.rag.ingestion import (
        csv_to_documents,
        DocumentSchema,
        register_csv_schema,
        format_doc,
        FileType,
        ChunkStrategy,
        register_chunker,
        ingest_file,
        ingest_csv,
        ingest_pdf,
        ingest_docx,
        ingest_md,
        ingest_text,
    )
    _INGESTION_AVAILABLE = True
except ImportError:
    csv_to_documents = None
    DocumentSchema = None
    register_csv_schema = None
    format_doc = None
    FileType = None
    ChunkStrategy = None
    register_chunker = None
    ingest_file = None
    ingest_csv = None
    ingest_pdf = None
    ingest_docx = None
    ingest_md = None
    ingest_text = None
    _INGESTION_AVAILABLE = False

# Auto-register CSV schema converters (restaurant, travel, support, etc.)
# These are registered when the schemas module is imported
try:
    from artemis.rag.ingestion.converters import schemas  # noqa: F401
except ImportError:
    # CSV schemas module not available or not yet implemented
    pass

# Auto-register retrieval strategies (semantic, keyword, hybrid)
# These are registered when the strategies module is imported
try:
    from artemis.rag import strategies  # noqa: F401
except ImportError:
    # Strategies module not available or not yet implemented
    pass

__all__ = []

# Add ingestion components to exports if available
if _INGESTION_AVAILABLE:
    __all__.extend([
        "csv_to_documents",
        "DocumentSchema",
        "register_csv_schema",
        "format_doc",
        "FileType",
        "ChunkStrategy",
        "register_chunker",
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
