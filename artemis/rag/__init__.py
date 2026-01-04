"""
RAG (Retrieval Augmented Generation) module for A.R.T.E.M.I.S.

This module provides a clean interface to all RAG functionality:
- Document conversion (core/document_converter.py)
- Document indexing (core/indexer.py)
- Document retrieval (core/retriever.py)
- Schema converters (converters/)
- Retrieval strategies (strategies/)
"""

# Import from core module (re-exports for backward compatibility)
from artemis.rag.core import (
    csv_to_documents,
    DocumentSchema,
    register_schema,
    format_doc,
)

# Re-export core components for backward compatibility
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

# Auto-register additional converters (travel, support, etc.)
# These are registered when the converters module is imported
try:
    from artemis.rag import converters  # noqa: F401
except ImportError:
    # Converters module not available or not yet implemented
    pass

# Auto-register retrieval strategies (semantic, keyword, hybrid)
# These are registered when the strategies module is imported
try:
    from artemis.rag import strategies  # noqa: F401
except ImportError:
    # Strategies module not available or not yet implemented
    pass

__all__ = [
    "csv_to_documents",
    "DocumentSchema",
    "register_schema",
    "format_doc",
]

# Add retriever and ingestion to exports if available
if _RETRIEVER_AVAILABLE:
    __all__.extend(["Retriever", "RetrievalMode", "Indexer", "register_strategy"])

