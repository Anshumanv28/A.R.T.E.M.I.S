"""
Template: Custom Retrieval Strategy for A.R.T.E.M.I.S.

This template shows how to create a custom retrieval strategy.
Copy this file and customize it for your specific search method.

Usage:
1. Copy this file to your project (e.g., my_project/my_strategy.py)
   OR add it to artemis/rag/strategies/ if contributing to A.R.T.E.M.I.S.
2. Customize the search logic
3. Import it in your code before using
4. Use it with Retriever

Example:
    from my_project.my_strategy import my_custom_search
    from artemis.rag import Retriever, RetrievalMode
    
    retriever = Retriever(mode=RetrievalMode.MY_MODE)
    results = retriever.retrieve("your query", k=5)
"""

from typing import List, Dict, Any
from artemis.rag.core.retriever import (
    register_strategy,
    RetrievalMode,
    Retriever
)
from artemis.utils import get_logger

logger = get_logger(__name__)

# TODO: Choose or create your retrieval mode
# Option 1: Use existing mode
# MODE = RetrievalMode.SEMANTIC  # or RetrievalMode.KEYWORD, RetrievalMode.HYBRID

# Option 2: Create new mode (you'll need to add it to RetrievalMode enum first)
# MODE = RetrievalMode("my_custom_mode")


@register_strategy(RetrievalMode.SEMANTIC)  # TODO: Change to your mode
def my_custom_search(
    retriever: Retriever,
    query: str,
    k: int = 5,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Custom search implementation.
    
    TODO: Update this docstring with your strategy's description.
    
    Args:
        retriever: Retriever instance providing:
            - qdrant_client: QdrantClient instance for vector database access
            - collection_name: str - Name of the collection to search
            - embedder: Embedder instance for generating embeddings
        query: Search query string
        k: Number of results to return (default: 5)
        **kwargs: Additional search parameters
            - score_threshold: float - Minimum score threshold
            - filter: Dict - Qdrant filter conditions
            - Other custom parameters
    
    Returns:
        List of dictionaries, each containing:
        - text: str - Document text content
        - score: float - Relevance score (higher is better)
        - metadata: Dict - Document metadata for filtering
    """
    # TODO: Access retriever resources
    qdrant_client = retriever.qdrant_client
    collection_name = retriever.collection_name
    embedder = retriever.embedder
    
    logger.debug(f"Searching for '{query}' with k={k}")
    
    # TODO: Implement your search logic
    # Example: Semantic vector search
    
    # Step 1: Generate query embedding
    query_embeddings = embedder.embed([query])
    query_vector = query_embeddings[0]
    
    # Step 2: Build search parameters
    score_threshold = kwargs.get("score_threshold", None)
    filter_conditions = kwargs.get("filter", None)
    
    # Step 3: Perform search in Qdrant
    search_params = {
        "collection_name": collection_name,
        "query_vector": query_vector,
        "limit": k,
    }
    
    if score_threshold is not None:
        search_params["score_threshold"] = score_threshold
    
    if filter_conditions is not None:
        search_params["query_filter"] = filter_conditions
    
    # Additional Qdrant search parameters can be added here
    # See Qdrant documentation for available options
    
    try:
        results = qdrant_client.search(**search_params)
    except Exception as e:
        logger.exception(f"Search failed: {e}")
        raise
    
    # Step 4: Format results
    formatted_results = []
    for result in results:
        # Extract payload data
        payload = result.payload or {}
        text = payload.get("text", "")
        metadata = payload.get("metadata", {})
        score = result.score
        
        formatted_results.append({
            "text": text,
            "score": float(score),
            "metadata": metadata
        })
    
    logger.info(f"Found {len(formatted_results)} results")
    return formatted_results


# Alternative: Keyword-based search example
# This would require additional dependencies (e.g., BM25, TF-IDF)
"""
@register_strategy(RetrievalMode.KEYWORD)
def my_keyword_search(
    retriever: Retriever,
    query: str,
    k: int = 5,
    **kwargs
) -> List[Dict[str, Any]]:
    # TODO: Implement keyword search (BM25, TF-IDF, etc.)
    # This would require:
    # 1. Building an index from stored documents
    # 2. Tokenizing the query
    # 3. Scoring documents based on keyword matches
    # 4. Returning top k results
    
    pass
"""


# Alternative: Hybrid search example
# Combines semantic and keyword search
"""
@register_strategy(RetrievalMode.HYBRID)
def my_hybrid_search(
    retriever: Retriever,
    query: str,
    k: int = 5,
    **kwargs
) -> List[Dict[str, Any]]:
    # TODO: Implement hybrid search
    # This would:
    # 1. Perform semantic search
    # 2. Perform keyword search
    # 3. Combine and rerank results
    # 4. Return top k results
    
    semantic_weight = kwargs.get("semantic_weight", 0.7)
    keyword_weight = kwargs.get("keyword_weight", 0.3)
    
    # Get results from both strategies
    # semantic_results = semantic_search(...)
    # keyword_results = keyword_search(...)
    
    # Combine and rerank
    # combined_results = combine_results(semantic_results, keyword_results, ...)
    
    pass
"""


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     from artemis.rag import Retriever, RetrievalMode, Indexer
#     
#     # Create retriever with your custom strategy
#     indexer = Indexer(collection_name="test_collection")
#     retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
#     
#     # Perform search
#     results = retriever.retrieve("your search query", k=5)
#     
#     # Print results
#     for i, result in enumerate(results, 1):
#         print(f"\nResult {i}:")
#         print(f"Score: {result['score']:.4f}")
#         print(f"Text: {result['text'][:100]}...")
#         print(f"Metadata: {result['metadata']}")
