"""
Semantic search strategy for A.R.T.E.M.I.S.

Implements semantic vector search using embeddings and Qdrant.
This is the primary retrieval strategy for MVP.
"""

from typing import List, Dict, Any

from artemis.rag.core.retriever import register_strategy, RetrievalMode, Retriever
from artemis.rag.core.query_parser import parse_query
from artemis.rag.core.filter_builder import build_qdrant_filter
from artemis.utils import get_logger

logger = get_logger(__name__)


@register_strategy(RetrievalMode.SEMANTIC)
def semantic_search_strategy(retriever: Retriever, query: str, k: int) -> List[Dict[str, Any]]:
    """
    Perform semantic vector search using Qdrant.
    
    This is the default strategy for semantic search. It uses sentence
    transformers to generate query embeddings and searches for similar
    documents in the Qdrant vector database.
    
    Args:
        retriever: Retriever instance (provides access to qdrant_client, embedder, etc.)
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of dictionaries containing:
        - 'text': Document text content
        - 'score': Similarity score (higher is better)
        - 'metadata': Document metadata (excluding 'text' field)
        
    Raises:
        ValueError: If embedding model is not available
        
    Example:
        >>> retriever = Retriever(mode=RetrievalMode.SEMANTIC)
        >>> results = retriever.retrieve("Italian restaurants in Mumbai", k=5)
        >>> for result in results:
        ...     print(f"Score: {result['score']:.4f}")
        ...     print(f"Text: {result['text'][:100]}...")
    """
    logger.debug(f"Performing semantic search: query='{query[:50]}...', k={k}")
    
    if retriever.embedder is None:
        raise ValueError("Embedder is required for semantic search")
    
    try:
        # Parse query to extract filter conditions
        cleaned_query, filter_conditions = parse_query(query)
        
        # Build Qdrant filter if conditions found
        qdrant_filter = None
        if filter_conditions:
            try:
                qdrant_filter = build_qdrant_filter(filter_conditions)
                if qdrant_filter:
                    logger.debug(f"Applied metadata filter with {len(filter_conditions)} condition(s)")
            except Exception as e:
                logger.warning(f"Failed to build Qdrant filter: {e}. Proceeding without filter.")
                qdrant_filter = None
        
        # Generate query embedding (use cleaned query if filters were extracted)
        query_for_embedding = cleaned_query if filter_conditions else query
        query_embedding = retriever.embedder.encode_single(query_for_embedding)
        logger.debug("Generated query embedding")
        
        # Search in Qdrant using query_points with optional filter
        query_params = {
            "collection_name": retriever.collection_name,
            "query": query_embedding,
            "limit": k,
        }
        
        # Add filter if available
        if qdrant_filter:
            query_params["query_filter"] = qdrant_filter
        
        try:
            query_response = retriever.qdrant_client.query_points(**query_params)
            search_results = query_response.points
            logger.debug(f"Qdrant search returned {len(search_results)} results")
        except Exception as e:
            # Check if error is about missing index
            error_str = str(e).lower()
            if "index required" in error_str or "index not found" in error_str:
                logger.warning(
                    f"Metadata index missing for filter. Error: {e}. "
                    "Retrying without filter. Consider creating indexes for metadata fields."
                )
                # Retry without filter
                query_params.pop("query_filter", None)
                query_response = retriever.qdrant_client.query_points(**query_params)
                search_results = query_response.points
                logger.debug(f"Qdrant search (without filter) returned {len(search_results)} results")
            else:
                # Re-raise other errors
                raise
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "text": result.payload.get("text", ""),
                "score": result.score,
                "metadata": {k: v for k, v in result.payload.items() if k != "text"},
            })
        
        if results:
            logger.debug(f"Top result score: {results[0]['score']:.4f}")
        
        return results
    except Exception as e:
        logger.exception(
            f"Error during semantic search: query='{query[:50]}...'",
            exc_info=True
        )
        raise

