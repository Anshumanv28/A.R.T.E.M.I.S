"""
DOCX metadata extractor for A.R.T.E.M.I.S.
"""

from typing import List, Dict, Any

from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)


class DOCXMetadataExtractor(MetadataExtractor):
    """Extract metadata from DOCX structure (paragraph styles, etc.)."""
    
    def extract(self, text: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract paragraph styles and structure from DOCX.
        
        Args:
            text: Extracted DOCX text content
            **kwargs: Additional arguments (chunk_indices, paragraph_styles, etc.)
            
        Returns:
            List of metadata dictionaries with paragraph styles, sections
        """
        chunk_indices = kwargs.get('chunk_indices', [])
        num_chunks = len(chunk_indices) if chunk_indices else 1
        
        paragraph_styles = kwargs.get('paragraph_styles', {})
        
        metadata_list = []
        for i in range(num_chunks):
            meta = {
                "source_type": "docx",
            }
            
            if paragraph_styles and i in paragraph_styles:
                meta["paragraph_style"] = paragraph_styles[i]
            
            metadata_list.append(meta)
        
        logger.debug(f"Extracted metadata for {len(metadata_list)} DOCX chunks")
        return metadata_list

