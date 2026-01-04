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

# Import retriever and ingestion (requires qdrant_client - optional)
try:
    from artemis.rag.core.retrieval import Retriever, RetrievalMode, register_strategy
    from artemis.rag.core.ingestion import Ingester
    _RETRIEVER_AVAILABLE = True
except ImportError:
    # Retriever/Ingester not available if qdrant_client is not installed
    Retriever = None
    RetrievalMode = None
    register_strategy = None
    Ingester = None
    _RETRIEVER_AVAILABLE = False

__all__ = [
    "csv_to_documents",
    "DocumentSchema",
    "register_schema",
    "format_doc",
]

# Add retriever and ingestion to exports if available
if _RETRIEVER_AVAILABLE:
    __all__.extend(["Retriever", "RetrievalMode", "Ingester", "register_strategy"])

