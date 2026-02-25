"""
RAG tools for agent use.

Thin callable wrappers around Retriever, Indexer/ingest_file, and collection_manager
so the agent can search, ingest, and manage collections via a tool-calling node.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from artemis.utils import get_logger

logger = get_logger(__name__)

# Optional imports so tools can be used when deps are available
try:
    from artemis.rag.core import Retriever, Indexer
    from artemis.rag.core.collection_manager import (
        list_collections,
        get_collection_info,
        create_collection,
        clear_collection,
        delete_collection,
    )
    from artemis.rag.ingestion import ingest_file, FileType
    _TOOLS_AVAILABLE = True
except ImportError:
    Retriever = None
    Indexer = None
    list_collections = None
    get_collection_info = None
    create_collection = None
    clear_collection = None
    delete_collection = None
    ingest_file = None
    FileType = None
    _TOOLS_AVAILABLE = False


def create_rag_search_tool(
    retriever: "Retriever",
    k: int = 5,
) -> Callable[[str], List[Dict[str, Any]]]:
    """
    Create a search tool that queries the knowledge base.

    Returns a callable (query: str) -> list[dict] with keys text, score, metadata.
    Use this as the RAG search tool when registering tools for the agent.
    """
    def search(query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant documents."""
        return retriever.retrieve(query, k=k)

    return search


def create_rag_ingest_tool(
    indexer: "Indexer",
) -> Callable[[str, str], Dict[str, Any]]:
    """
    Create an ingest tool that adds a file to the RAG collection.

    Returns a callable (path: str, file_type: str) -> dict.
    file_type must be one of: csv, pdf, docx, md, text.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    _FILE_TYPE_MAP = {
        "csv": FileType.CSV,
        "pdf": FileType.PDF,
        "docx": FileType.DOCX,
        "md": FileType.MD,
        "text": FileType.TEXT,
    }

    def ingest(path: str, file_type: str) -> Dict[str, Any]:
        """Ingest a file into the knowledge base."""
        path_obj = Path(path)
        if not path_obj.exists():
            return {"ok": False, "error": f"File not found: {path}"}
        ft_lower = file_type.strip().lower()
        if ft_lower not in _FILE_TYPE_MAP:
            return {
                "ok": False,
                "error": f"Unsupported file_type '{file_type}'. Use one of: csv, pdf, docx, md, text",
            }
        try:
            ingest_file(path_obj, _FILE_TYPE_MAP[ft_lower], indexer)
            return {"ok": True, "path": path, "file_type": ft_lower}
        except Exception as e:
            logger.exception(f"Ingest failed for {path}: {e}")
            return {"ok": False, "error": str(e), "path": path}

    return ingest


def list_collections_tool() -> List[str]:
    """
    List all Qdrant collection names.

    Uses QDRANT_URL and QDRANT_API_KEY from environment.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return list_collections()


def get_collection_info_tool(collection_name: str) -> Dict[str, Any]:
    """
    Get information about a collection (points count, status, etc.).

    Uses Qdrant env vars.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return get_collection_info(collection_name)


def create_collection_tool(
    collection_name: str,
    embedding_dim: Optional[int] = None,
) -> bool:
    """
    Create a new Qdrant collection.

    Uses Qdrant env vars. embedding_dim defaults to embedder dimension if not set.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return create_collection(
        collection_name=collection_name,
        embedding_dim=embedding_dim,
    )


def clear_collection_tool(
    collection_name: str,
    confirm: bool = False,
) -> bool:
    """
    Clear all points from a collection (keeps the collection).

    Requires confirm=True. Only set confirm after user has approved.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return clear_collection(
        collection_name=collection_name,
        confirm=confirm,
    )


def delete_collection_tool(
    collection_name: str,
    confirm: bool = False,
) -> bool:
    """
    Delete a collection entirely.

    Requires confirm=True. Only set confirm after user has approved.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return delete_collection(
        collection_name=collection_name,
        confirm=confirm,
    )


__all__ = [
    "create_rag_search_tool",
    "create_rag_ingest_tool",
    "list_collections_tool",
    "get_collection_info_tool",
    "create_collection_tool",
    "clear_collection_tool",
    "delete_collection_tool",
]
