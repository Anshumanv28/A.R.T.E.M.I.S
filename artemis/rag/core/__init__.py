"""
Core RAG components for A.R.T.E.M.I.S.

This module contains the core RAG functionality: embedding, indexing, and retrieval.
"""

# Import embedder (requires sentence_transformers - optional)
try:
    from artemis.rag.core.embedder import Embedder
    _EMBEDDER_AVAILABLE = True
except ImportError:
    # Embedder not available if sentence_transformers is not installed
    Embedder = None
    _EMBEDDER_AVAILABLE = False

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

# Import collection manager (requires qdrant_client - optional)
try:
    from artemis.rag.core.collection_manager import (
        list_collections,
        get_collection_info,
        delete_collection,
        clear_collection,
        create_collection,
        get_qdrant_client
    )
    _COLLECTION_MANAGER_AVAILABLE = True
except ImportError:
    # Collection manager not available if qdrant_client is not installed
    list_collections = None
    get_collection_info = None
    delete_collection = None
    clear_collection = None
    create_collection = None
    get_qdrant_client = None
    _COLLECTION_MANAGER_AVAILABLE = False

__all__ = []

# Add embedder to exports if available
if _EMBEDDER_AVAILABLE:
    __all__.append("Embedder")

# Add retriever and indexer to exports if available
if _RETRIEVER_AVAILABLE:
    __all__.extend(["Retriever", "RetrievalMode", "Indexer", "register_strategy"])

# Add collection manager to exports if available
if _COLLECTION_MANAGER_AVAILABLE:
    __all__.extend([
        "list_collections",
        "get_collection_info",
        "delete_collection",
        "clear_collection",
        "create_collection",
        "get_qdrant_client"
    ])
