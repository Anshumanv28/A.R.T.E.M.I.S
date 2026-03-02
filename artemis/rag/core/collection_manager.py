"""
Collection management utilities for Qdrant.

Provides functions to list, delete, clear, and get info about Qdrant collections.
"""

import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import CollectionInfo, PointsSelector, PointIdsList, VectorParams, Distance

from artemis.utils import get_logger

logger = get_logger(__name__)


def get_qdrant_client(
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None
) -> QdrantClient:
    """
    Get Qdrant client instance.
    
    Args:
        qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
        qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        
    Returns:
        QdrantClient instance
        
    Raises:
        ValueError: If QDRANT_URL is not set
    """
    qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
    qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        raise ValueError(
            "QDRANT_URL is required. Set it in environment or pass qdrant_url parameter."
        )
    
    return QdrantClient(url=qdrant_url, api_key=qdrant_api_key)


def create_collection(
    collection_name: str,
    embedding_dim: Optional[int] = None,
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None
) -> bool:
    """
    Create a new Qdrant collection.
    
    If embedding_dim is not provided, uses the default embedder dimension (384 for all-MiniLM-L6-v2).
    Idempotent: if the collection already exists (or Qdrant returns 409), returns True without raising.
    
    Args:
        collection_name: Name of the collection to create
        embedding_dim: Embedding dimension (defaults to 384 if not provided)
        qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
        qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        
    Returns:
        True if collection was created or already exists
        
    Raises:
        ValueError: If collection_name is empty
        Exception: If creation fails (other than already exists)
    """
    name = (collection_name or "").strip()
    if not name:
        raise ValueError("collection_name is required and cannot be empty")

    client = get_qdrant_client(qdrant_url, qdrant_api_key)

    try:
        existing_collections = list_collections(qdrant_url, qdrant_api_key)
        if name in existing_collections:
            logger.info(f"Collection '{name}' already exists; no-op.")
            return True
    except Exception:
        # If listing fails, try to get collection directly
        try:
            client.get_collection(name)
            logger.info(f"Collection '{name}' already exists; no-op.")
            return True
        except Exception:
            # Collection doesn't exist, proceed with creation
            pass

    # Get embedding dimension
    if embedding_dim is None:
        # Use default embedder dimension (all-MiniLM-L6-v2 = 384)
        try:
            from artemis.rag.core.embedder import Embedder
            embedder = Embedder()  # Uses default model
            embedding_dim = embedder.get_dimension()
            logger.info(f"Using default embedder dimension: {embedding_dim}")
        except Exception as e:
            logger.warning(f"Could not get embedder dimension, using default 384: {e}")
            embedding_dim = 384  # Default for all-MiniLM-L6-v2
    
    try:
        logger.info(
            f"Creating Qdrant collection '{name}' "
            f"with embedding dimension {embedding_dim}"
        )

        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        )

        logger.info(f"Successfully created collection '{name}'")
        return True

    except Exception as e:
        err_str = str(e).lower()
        # Qdrant returns 409 when collection already exists; treat as success (idempotent)
        if "409" in err_str or "already exists" in err_str or "conflict" in err_str:
            logger.info(f"Collection '{name}' already exists (Qdrant 409); no-op.")
            return True
        logger.exception(f"Failed to create collection: {e}")
        raise


def list_collections(
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None
) -> List[str]:
    """
    List all collection names in Qdrant.
    
    Args:
        qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
        qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        
    Returns:
        List of collection names
        
    Raises:
        Exception: If connection fails
    """
    client = get_qdrant_client(qdrant_url, qdrant_api_key)
    
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        logger.info(f"Found {len(collection_names)} collections")
        return collection_names
    except Exception as e:
        logger.exception(f"Failed to list collections: {e}")
        raise


def get_collection_info(
    collection_name: str,
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get information about a collection.
    
    Args:
        collection_name: Name of the collection
        qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
        qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        
    Returns:
        Dictionary with collection information (name, points_count, etc.)
        
    Raises:
        ValueError: If collection doesn't exist
        Exception: If connection fails
    """
    client = get_qdrant_client(qdrant_url, qdrant_api_key)
    
    try:
        collection_info = client.get_collection(collection_name)
        info = {
            "name": collection_name,
            "points_count": collection_info.points_count,
            "vectors_count": collection_info.vectors_count if hasattr(collection_info, 'vectors_count') else collection_info.points_count,
            "status": str(collection_info.status) if hasattr(collection_info, 'status') else "unknown",
        }
        logger.info(f"Collection '{collection_name}': {collection_info.points_count} points")
        return info
    except Exception as e:
        error_str = str(e).lower()
        if "not found" in error_str or "doesn't exist" in error_str:
            raise ValueError(
                f"Collection '{collection_name}' does not exist in Qdrant (it was not found; this does not mean it was deleted)."
            ) from e
        logger.exception(f"Failed to get collection info: {e}")
        raise


def delete_collection(
    collection_name: str,
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None,
    confirm: bool = False
) -> bool:
    """
    Delete an entire collection from Qdrant.
    
    WARNING: This operation is permanent and cannot be undone!
    
    Args:
        collection_name: Name of the collection to delete
        qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
        qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        confirm: If False, raises ValueError. Set to True to confirm deletion.
        
    Returns:
        True if deletion was successful
        
    Raises:
        ValueError: If confirm is False or collection doesn't exist
        Exception: If deletion fails
    """
    if not confirm:
        raise ValueError(
            f"Deletion requires confirmation. Set confirm=True to delete collection '{collection_name}'"
        )
    
    client = get_qdrant_client(qdrant_url, qdrant_api_key)
    
    try:
        # Check if collection exists
        try:
            info = client.get_collection(collection_name)
            points_count = info.points_count
        except Exception:
            points_count = 0
        
        logger.warning(f"Deleting collection '{collection_name}' with {points_count} points")
        client.delete_collection(collection_name)
        logger.info(f"Successfully deleted collection '{collection_name}'")
        return True
    except Exception as e:
        error_str = str(e).lower()
        if "not found" in error_str or "doesn't exist" in error_str:
            raise ValueError(
                f"Collection '{collection_name}' does not exist in Qdrant (not found; not necessarily deleted)."
            ) from e
        logger.exception(f"Failed to delete collection: {e}")
        raise


def clear_collection(
    collection_name: str,
    qdrant_url: Optional[str] = None,
    qdrant_api_key: Optional[str] = None,
    confirm: bool = False
) -> bool:
    """
    Clear all points from a collection but keep the collection.
    
    WARNING: This operation is permanent and cannot be undone!
    
    Args:
        collection_name: Name of the collection to clear
        qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
        qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
        confirm: If False, raises ValueError. Set to True to confirm clearing.
        
    Returns:
        True if clearing was successful
        
    Raises:
        ValueError: If confirm is False or collection doesn't exist
        Exception: If clearing fails
    """
    if not confirm:
        raise ValueError(
            f"Clearing requires confirmation. Set confirm=True to clear collection '{collection_name}'"
        )
    
    client = get_qdrant_client(qdrant_url, qdrant_api_key)
    
    try:
        # Check if collection exists
        info = client.get_collection(collection_name)
        points_count = info.points_count
        
        if points_count == 0:
            logger.info(f"Collection '{collection_name}' is already empty")
            return True
        
        logger.warning(f"Clearing {points_count} points from collection '{collection_name}'")
        
        # Get all point IDs by scrolling
        point_ids = []
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=100,
            with_payload=False,
            with_vectors=False
        )
        
        points = scroll_result[0]
        while points:
            point_ids.extend([point.id for point in points])
            
            # Get next batch if there are more points
            if scroll_result[1]:  # next_page_offset exists
                scroll_result = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=scroll_result[1],
                    with_payload=False,
                    with_vectors=False
                )
                points = scroll_result[0]
            else:
                break
        
        # Delete all points
        if point_ids:
            # Delete in batches to avoid overwhelming the API
            batch_size = 1000
            for i in range(0, len(point_ids), batch_size):
                batch = point_ids[i:i + batch_size]
                try:
                    # Try direct point IDs first (simpler API)
                    client.delete(
                        collection_name=collection_name,
                        points_selector=batch
                    )
                except (TypeError, AttributeError):
                    # Fallback to PointsSelector if direct list doesn't work
                    client.delete(
                        collection_name=collection_name,
                        points_selector=PointsSelector(
                            points=PointIdsList(points=batch)
                        )
                    )
            logger.info(f"Successfully cleared {len(point_ids)} points from collection '{collection_name}'")
        
        return True
    except Exception as e:
        error_str = str(e).lower()
        if "not found" in error_str or "doesn't exist" in error_str:
            raise ValueError(
                f"Collection '{collection_name}' does not exist in Qdrant (not found; not necessarily deleted)."
            ) from e
        logger.exception(f"Failed to clear collection: {e}")
        raise
