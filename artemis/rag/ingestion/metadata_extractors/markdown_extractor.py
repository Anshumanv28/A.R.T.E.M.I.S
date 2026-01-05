"""
Markdown metadata extractor for A.R.T.E.M.I.S.
"""

from typing import List, Dict, Any, Tuple, Optional

from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)


class MarkdownMetadataExtractor(MetadataExtractor):
    """Extract metadata from Markdown structure (header hierarchy, sections)."""
    
    def extract(
        self,
        text: str,
        headers: Optional[List[Tuple[int, str]]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract heading hierarchy and sections from Markdown.
        
        Args:
            text: Markdown text content
            headers: Optional list of (level, header_text) tuples
            **kwargs: Additional arguments (chunk_indices, etc.)
            
        Returns:
            List of metadata dictionaries with header hierarchy, sections
        """
        chunk_indices = kwargs.get('chunk_indices', [])
        num_chunks = len(chunk_indices) if chunk_indices else 1
        
        metadata_list = []
        for i in range(num_chunks):
            meta = {
                "source_type": "markdown",
            }
            
            if headers:
                # Map chunk to nearest header (simplified - could be improved)
                meta["headers"] = [h[1] for h in headers]
            
            metadata_list.append(meta)
        
        logger.debug(f"Extracted metadata for {len(metadata_list)} Markdown chunks")
        return metadata_list

