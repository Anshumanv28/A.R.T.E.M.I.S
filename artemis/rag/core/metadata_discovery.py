"""
Metadata discovery for adaptive filtering in A.R.T.E.M.I.S.

Automatically discovers metadata fields and their types by sampling
documents from Qdrant collections, enabling filtering to work with
any dataset without hardcoded field names.
"""

from typing import Dict, Set, Optional, Any
from collections import Counter

from qdrant_client import QdrantClient
from artemis.utils import get_logger

logger = get_logger(__name__)


class MetadataDiscovery:
    """
    Discovers metadata fields and types from Qdrant collections.
    
    Samples documents to automatically detect:
    - Field names (all keys in payload except 'text')
    - Field types (string, number, boolean)
    
    Results are cached per collection to avoid repeated sampling.
    """
    
    def __init__(self, qdrant_client: QdrantClient, collection_name: str):
        """
        Initialize metadata discovery.
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of the collection to discover fields from
        """
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self._cache: Dict[str, Dict[str, str]] = {}  # collection_name -> {field: type}
    
    def discover_fields(self, sample_size: int = 100) -> Dict[str, str]:
        """
        Discover metadata fields by sampling documents from the collection.
        
        Samples documents and analyzes their payload to detect:
        - Field names (all keys except 'text')
        - Field types: 'string', 'number', 'boolean'
        
        Args:
            sample_size: Number of documents to sample (default: 100)
            
        Returns:
            Dictionary mapping field names to types: {field_name: 'string'|'number'|'boolean'}
        """
        # Check cache first
        cache_key = self.collection_name
        if cache_key in self._cache:
            logger.debug(f"Using cached field discovery for collection '{self.collection_name}'")
            return self._cache[cache_key]
        
        logger.debug(f"Discovering metadata fields from collection '{self.collection_name}' (sampling {sample_size} documents)")
        
        try:
            # Sample documents from the collection
            # Use scroll to get a sample of documents
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=sample_size,
                with_payload=True,
                with_vectors=False,
            )
            
            points = scroll_result[0]  # First element is list of points
            
            if not points:
                logger.warning(f"No documents found in collection '{self.collection_name}' for field discovery")
                self._cache[cache_key] = {}
                return {}
            
            # Analyze payloads to discover fields and types
            field_types: Dict[str, Set[str]] = {}  # field_name -> set of observed types
            
            for point in points:
                payload = point.payload or {}
                
                # Skip 'text' field (it's the document content, not metadata)
                for field_name, field_value in payload.items():
                    if field_name == "text":
                        continue
                    
                    # Detect type
                    if field_name not in field_types:
                        field_types[field_name] = set()
                    
                    if isinstance(field_value, bool):
                        field_types[field_name].add("boolean")
                    elif isinstance(field_value, (int, float)):
                        field_types[field_name].add("number")
                    elif isinstance(field_value, str):
                        field_types[field_name].add("string")
                    elif field_value is None:
                        # None values don't tell us the type, skip
                        continue
                    else:
                        # Unknown type, treat as string
                        field_types[field_name].add("string")
            
            # Determine final type for each field
            # Priority: boolean > number > string
            discovered_fields: Dict[str, str] = {}
            for field_name, types in field_types.items():
                if "boolean" in types:
                    discovered_fields[field_name] = "boolean"
                elif "number" in types:
                    discovered_fields[field_name] = "number"
                else:
                    discovered_fields[field_name] = "string"
            
            # Cache results
            self._cache[cache_key] = discovered_fields
            
            logger.info(
                f"Discovered {len(discovered_fields)} metadata fields in collection '{self.collection_name}': "
                f"{', '.join(discovered_fields.keys())}"
            )
            logger.debug(f"Field types: {discovered_fields}")
            
            return discovered_fields
            
        except Exception as e:
            logger.warning(
                f"Failed to discover metadata fields from collection '{self.collection_name}': {e}. "
                "Filtering may not work correctly."
            )
            # Return empty dict on error - filtering will fall back gracefully
            self._cache[cache_key] = {}
            return {}
    
    def get_field_type(self, field_name: str, discovered_fields: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Get the type of a specific field.
        
        Args:
            field_name: Name of the field
            discovered_fields: Optional pre-discovered fields dict (to avoid re-discovery)
            
        Returns:
            Field type ('string', 'number', 'boolean') or None if not found
        """
        if discovered_fields is None:
            discovered_fields = self.discover_fields()
        
        return discovered_fields.get(field_name)
    
    def clear_cache(self, collection_name: Optional[str] = None) -> None:
        """
        Clear the discovery cache.
        
        Args:
            collection_name: Optional specific collection to clear. If None, clears all.
        """
        if collection_name:
            self._cache.pop(collection_name, None)
            logger.debug(f"Cleared discovery cache for collection '{collection_name}'")
        else:
            self._cache.clear()
            logger.debug("Cleared all discovery cache")
