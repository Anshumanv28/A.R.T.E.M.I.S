"""
Hybrid search strategy for A.R.T.E.M.I.S.

Combines semantic vector search and BM25 keyword search for optimal results.
"""

import numpy as np
from typing import List, Dict, Any

from artemis.rag.core.retriever import register_strategy, RetrievalMode, Retriever
from artemis.rag.strategies.semantic import semantic_search_strategy
from artemis.rag.strategies.keyword import keyword_search_strategy, BM25_AVAILABLE
from artemis.utils import get_logger

logger = get_logger(__name__)


def _normalize_scores(scores: List[float]) -> List[float]:
    """Normalize scores to 0-1 range."""
    if not scores:
        return scores
    scores_array = np.array(scores)
    min_score = scores_array.min()
    max_score = scores_array.max()
    if max_score == min_score:
        return [1.0] * len(scores)
    return ((scores_array - min_score) / (max_score - min_score)).tolist()


def _combine_results(
    semantic_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Combine semantic and keyword search results.
    
    Args:
        semantic_results: Results from semantic search
        keyword_results: Results from keyword search
        semantic_weight: Weight for semantic scores (default 0.7)
        keyword_weight: Weight for keyword scores (default 0.3)
        
    Returns:
        Combined and re-ranked results
    """
    # Create a map of text -> result for deduplication
    combined_map: Dict[str, Dict[str, Any]] = {}
    
    # Normalize semantic scores
    if semantic_results:
        semantic_scores = [r['score'] for r in semantic_results]
        normalized_semantic = _normalize_scores(semantic_scores)
        
        for result, norm_score in zip(semantic_results, normalized_semantic):
            text = result['text']
            combined_map[text] = {
                'text': text,
                'metadata': result.get('metadata', {}),
                'semantic_score': norm_score,
                'keyword_score': 0.0,
                'combined_score': norm_score * semantic_weight,
            }
    
    # Normalize keyword scores and merge
    if keyword_results:
        keyword_scores = [r['score'] for r in keyword_results]
        normalized_keyword = _normalize_scores(keyword_scores)
        
        for result, norm_score in zip(keyword_results, normalized_keyword):
            text = result['text']
            if text in combined_map:
                # Update existing entry
                combined_map[text]['keyword_score'] = norm_score
                combined_map[text]['combined_score'] = (
                    combined_map[text]['semantic_score'] * semantic_weight +
                    norm_score * keyword_weight
                )
            else:
                # New entry
                combined_map[text] = {
                    'text': text,
                    'metadata': result.get('metadata', {}),
                    'semantic_score': 0.0,
                    'keyword_score': norm_score,
                    'combined_score': norm_score * keyword_weight,
                }
    
    # Sort by combined score and return
    combined_results = list(combined_map.values())
    combined_results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # Format output (remove internal scores, keep only combined_score as 'score')
    formatted_results = []
    for result in combined_results:
        formatted_results.append({
            'text': result['text'],
            'score': result['combined_score'],
            'metadata': result['metadata'],
        })
    
    return formatted_results


@register_strategy(RetrievalMode.HYBRID)
def hybrid_search_strategy(
    retriever: Retriever, 
    query: str, 
    k: int,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining semantic and keyword search.
    
    Combines results from both semantic vector search and BM25 keyword search,
    providing the best of both worlds:
    - Semantic search for natural language understanding
    - Keyword search for exact term matching
    
    Args:
        retriever: Retriever instance
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of retrieved documents with combined scores and metadata
        
    Raises:
        ImportError: If rank_bm25 is not installed
    """
    if not BM25_AVAILABLE:
        raise ImportError(
            "rank_bm25 package is required for hybrid search. "
            "Install it with: pip install rank-bm25"
        )
    
    # Default weights: favor semantic search slightly
    semantic_weight = 0.7
    keyword_weight = 0.3
    
    logger.debug(f"Performing hybrid search: query='{query[:50]}...', k={k}, "
                f"semantic_weight={semantic_weight}, keyword_weight={keyword_weight}")
    
    # Get semantic results (fetch more than k to have better coverage)
    semantic_k = min(k * 2, 50)  # Get 2x results for better combination
    try:
        semantic_results = semantic_search_strategy(retriever, query, semantic_k)
    except Exception as e:
        logger.warning(f"Semantic search failed: {e}. Using keyword search only.")
        semantic_results = []
    
    # Get keyword results (fetch more than k to have better coverage)
    keyword_k = min(k * 2, 50)
    try:
        keyword_results = keyword_search_strategy(retriever, query, keyword_k)
    except Exception as e:
        logger.warning(f"Keyword search failed: {e}. Using semantic search only.")
        keyword_results = []
    
    # If one method fails, fall back to the other
    if not semantic_results and not keyword_results:
        logger.error("Both semantic and keyword search failed")
        return []
    
    if not semantic_results:
        logger.debug("Falling back to keyword search only")
        return keyword_results[:k]
    
    if not keyword_results:
        logger.debug("Falling back to semantic search only")
        return semantic_results[:k]
    
    # Combine results
    combined_results = _combine_results(
        semantic_results,
        keyword_results,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
    )
    
    # Return top k
    final_results = combined_results[:k]
    logger.debug(f"Hybrid search returned {len(final_results)} results")
    return final_results

