"""
Keyword search strategy for A.R.T.E.M.I.S.

Placeholder for BM25/TF-IDF based keyword search implementation.
This will be implemented in Phase 2.
"""

from typing import List, Dict, Any

from artemis.rag.core.retriever import register_strategy, RetrievalMode, Retriever
from artemis.utils import get_logger

logger = get_logger(__name__)


@register_strategy(RetrievalMode.KEYWORD)
def keyword_search_strategy(retriever: Retriever, query: str, k: int) -> List[Dict[str, Any]]:
    """
    Perform keyword-based search (BM25/TF-IDF).
    
    This is a placeholder for future implementation. When implemented,
    this strategy will use BM25 or TF-IDF algorithms for keyword-based
    document retrieval, which is better suited for exact term matching
    and technical queries.
    
    Args:
        retriever: Retriever instance
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of retrieved documents with scores and metadata
        
    Raises:
        NotImplementedError: Keyword search is not yet implemented
        
    Example (Future):
        >>> retriever = Retriever(mode=RetrievalMode.KEYWORD)
        >>> results = retriever.retrieve("API endpoint /users", k=5)
        >>> # Returns documents matching exact keywords
    """
    logger.warning(
        f"Keyword search requested but not implemented. "
        f"Query: '{query[:50]}...', k={k}"
    )
    raise NotImplementedError(
        "Keyword search (BM25/TF-IDF) is coming soon. "
        "Use RetrievalMode.SEMANTIC for now."
    )

