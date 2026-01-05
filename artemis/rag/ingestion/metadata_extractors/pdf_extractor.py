"""
PDF metadata extractor for A.R.T.E.M.I.S.
"""

from typing import List, Dict, Any, Optional

from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)


class PDFMetadataExtractor(MetadataExtractor):
    """Extract metadata from PDF structure (page numbers, sections)."""
    
    def extract(
        self,
        text: str,
        page_numbers: Optional[Dict[int, str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract page numbers and sections from PDF structure.
        
        Args:
            text: Extracted PDF text content
            page_numbers: Optional mapping of chunk indices to page numbers
            **kwargs: Additional arguments (chunk_indices, etc.)
            
        Returns:
            List of metadata dictionaries with page numbers, sections
        """
        chunk_indices = kwargs.get('chunk_indices', [])
        num_chunks = len(chunk_indices) if chunk_indices else 1
        
        metadata_list = []
        for i in range(num_chunks):
            meta = {
                "source_type": "pdf",
            }
            
            if page_numbers and i in page_numbers:
                meta["page_number"] = page_numbers[i]
            
            metadata_list.append(meta)
        
        logger.debug(f"Extracted metadata for {len(metadata_list)} PDF chunks")
        return metadata_list

