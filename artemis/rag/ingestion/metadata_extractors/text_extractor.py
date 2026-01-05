"""
Text metadata extractor for A.R.T.E.M.I.S.
"""

from typing import List, Dict, Any

from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)


class TextMetadataExtractor(MetadataExtractor):
    """Extract basic metadata from text files."""
    
    def extract(self, text: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract basic metadata from text.
        
        Args:
            text: Text content
            **kwargs: Additional arguments (chunk_indices, etc.)
            
        Returns:
            List of metadata dictionaries with basic source type
        """
        chunk_indices = kwargs.get('chunk_indices', [])
        num_chunks = len(chunk_indices) if chunk_indices else 1
        
        metadata_list = []
        for i in range(num_chunks):
            meta = {
                "source_type": "text",
            }
            metadata_list.append(meta)
        
        logger.debug(f"Extracted metadata for {len(metadata_list)} text chunks")
        return metadata_list

