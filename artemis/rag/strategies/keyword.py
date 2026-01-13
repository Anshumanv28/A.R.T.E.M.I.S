"""
Keyword search strategy for A.R.T.E.M.I.S.

Implements BM25-based keyword search for exact term matching.
"""

import re
from typing import List, Dict, Any, Optional

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from artemis.rag.core.retriever import register_strategy, RetrievalMode, Retriever
from artemis.utils import get_logger

logger = get_logger(__name__)

# Cache for BM25 indexes per collection
_bm25_cache: Dict[str, tuple] = {}  # collection_name -> (bm25_index, documents, point_ids)


def _get_all_documents_from_qdrant(retriever: Retriever) -> tuple:
    """
    Fetch all documents from Qdrant collection for BM25 indexing.
    
    Returns:
        Tuple of (documents, point_ids) where:
        - documents: List of document text strings
        - point_ids: List of corresponding Qdrant point IDs
    """
    collection_name = retriever.collection_name
    
    # Check cache first
    if collection_name in _bm25_cache:
        bm25_index, documents, point_ids = _bm25_cache[collection_name]
        logger.debug(f"Using cached BM25 index for collection '{collection_name}'")
        return documents, point_ids, bm25_index
    
    logger.debug(f"Fetching all documents from collection '{collection_name}' for BM25 indexing")
    
    # Use scroll API to get all points
    documents = []
    point_ids = []
    
    try:
        scroll_result = retriever.qdrant_client.scroll(
            collection_name=collection_name,
            limit=100,  # Fetch in batches
            with_payload=True,
            with_vectors=False,
        )
        
        points = scroll_result[0]
        while points:
            for point in points:
                # Extract text from payload
                if hasattr(point, 'payload') and point.payload:
                    text = point.payload.get('text', '')
                    if text:
                        documents.append(text)
                        point_ids.append(point.id)
            
            # Get next batch if there are more points
            if scroll_result[1]:  # next_page_offset exists
                scroll_result = retriever.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=scroll_result[1],
                    with_payload=True,
                    with_vectors=False,
                )
                points = scroll_result[0]
            else:
                break
                
    except Exception as e:
        logger.error(f"Failed to fetch documents from Qdrant: {e}")
        raise
    
    if not documents:
        logger.warning(f"No documents found in collection '{collection_name}'")
        return [], [], None
    
    logger.info(f"Fetched {len(documents)} documents from collection '{collection_name}'")
    
    # Tokenize documents for BM25
    tokenized_docs = [
        re.sub(r'[^a-zA-Z0-9\s]', '', doc.lower()).split() 
        for doc in documents
    ]
    
    # Build BM25 index
    bm25_index = BM25Okapi(tokenized_docs)
    
    # Cache the index
    _bm25_cache[collection_name] = (bm25_index, documents, point_ids)
    logger.debug(f"Cached BM25 index for collection '{collection_name}'")
    
    return documents, point_ids, bm25_index


@register_strategy(RetrievalMode.KEYWORD)
def keyword_search_strategy(retriever: Retriever, query: str, k: int) -> List[Dict[str, Any]]:
    """
    Perform keyword-based search using BM25.
    
    Fetches all documents from Qdrant, builds a BM25 index, and scores
    the query against all documents. Better suited for exact term matching
    and technical queries.
    
    Args:
        retriever: Retriever instance
        query: Search query string
        k: Number of results to return
        
    Returns:
        List of retrieved documents with scores and metadata
        
    Raises:
        ImportError: If rank_bm25 is not installed
        ValueError: If no documents found in collection
    """
    if not BM25_AVAILABLE:
        raise ImportError(
            "rank_bm25 package is required for keyword search. "
            "Install it with: pip install rank-bm25"
        )
    
    logger.debug(f"Performing keyword search: query='{query[:50]}...', k={k}")
    
    # Get all documents and build BM25 index
    documents, point_ids, bm25_index = _get_all_documents_from_qdrant(retriever)
    
    if not documents or bm25_index is None:
        logger.warning("No documents available for keyword search")
        return []
    
    # Tokenize query
    tokenized_query = re.sub(r'[^a-zA-Z0-9\s]', '', query.lower()).split()
    
    # Get BM25 scores
    bm25_scores = bm25_index.get_scores(tokenized_query)
    
    # Get top k results
    top_indices = bm25_scores.argsort()[-k:][::-1]
    
    # Format results
    results = []
    for idx in top_indices:
        if bm25_scores[idx] > 0:  # Only include documents with non-zero scores
            # Fetch full point data from Qdrant
            try:
                point = retriever.qdrant_client.retrieve(
                    collection_name=retriever.collection_name,
                    ids=[point_ids[idx]],
                    with_payload=True,
                )[0]
                
                payload = point.payload or {}
                text = payload.get('text', documents[idx])
                metadata = {k: v for k, v in payload.items() if k != 'text'}
                
                results.append({
                    'text': text,
                    'score': float(bm25_scores[idx]),
                    'metadata': metadata,
                })
            except Exception as e:
                logger.warning(f"Failed to retrieve point {point_ids[idx]}: {e}")
                # Fallback to document text
                results.append({
                    'text': documents[idx],
                    'score': float(bm25_scores[idx]),
                    'metadata': {},
                })
    
    logger.debug(f"Keyword search returned {len(results)} results")
    return results

