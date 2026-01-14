"""
Template: Custom Metadata Extractor for A.R.T.E.M.I.S.

This template shows how to create a custom metadata extractor.
Copy this file and customize it for your specific file type.

Usage:
1. Copy this file to your project (e.g., my_project/my_extractor.py)
2. Customize the extraction logic
3. Use it with chunkers or ingestion pipeline

Note: Metadata extractors are typically used internally by chunkers,
but you can create custom extractors for specialized use cases.

Example:
    from my_project.my_extractor import MyMetadataExtractor
    from artemis.rag import ingest_file, FileType, Indexer
    
    extractor = MyMetadataExtractor()
    metadata = extractor.extract(content, **kwargs)
"""

from typing import List, Dict, Any
from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)


class MyMetadataExtractor(MetadataExtractor):
    """
    Extract metadata from [File Type].
    
    TODO: Update this docstring with your extractor's description.
    """
    
    def extract(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract metadata for each chunk.
        
        TODO: Update this docstring with your extraction logic description.
        
        Args:
            content: File content (type depends on file type)
                - str for text files (PDF, DOCX, MD, TEXT)
                - pandas.DataFrame for CSV files
                - Other types as needed
            **kwargs: Additional extraction parameters
                - chunk_indices: List[int] - Indices of chunks
                - page_numbers: Dict[int, int] - Mapping of chunk index to page number
                - headers: List[Tuple[int, str]] - Header hierarchy
                - Other custom parameters
        
        Returns:
            List of metadata dictionaries (one per chunk)
            Each dictionary should contain:
            - source_type: str - Type of source (e.g., "pdf", "csv", "text")
            - chunk_index: int - Index of the chunk
            - Other relevant metadata fields
        """
        metadata_list = []
        
        # TODO: Implement your extraction logic
        
        # Example: Extract page numbers for PDF
        if "page_numbers" in kwargs:
            page_numbers = kwargs["page_numbers"]
            chunk_indices = kwargs.get("chunk_indices", list(range(len(page_numbers))))
            
            for i, chunk_idx in enumerate(chunk_indices):
                metadata = {
                    "source_type": "pdf",
                    "chunk_index": chunk_idx,
                    "page_number": page_numbers.get(chunk_idx, None),
                    # Add more metadata as needed...
                }
                metadata_list.append(metadata)
        
        # Example: Extract headers for Markdown
        elif "headers" in kwargs:
            headers = kwargs["headers"]  # List of (level, text) tuples
            chunk_indices = kwargs.get("chunk_indices", list(range(len(headers))))
            
            for i, chunk_idx in enumerate(chunk_indices):
                # Find nearest header for this chunk
                nearest_header = None
                if headers:
                    # Simple logic: use header at same index or previous
                    header_idx = min(chunk_idx, len(headers) - 1)
                    nearest_header = headers[header_idx]
                
                metadata = {
                    "source_type": "markdown",
                    "chunk_index": chunk_idx,
                    "header_level": nearest_header[0] if nearest_header else None,
                    "header_text": nearest_header[1] if nearest_header else None,
                    # Add more metadata as needed...
                }
                metadata_list.append(metadata)
        
        # Example: Extract row data for CSV
        elif hasattr(content, 'iterrows'):  # pandas.DataFrame
            for idx, row in content.iterrows():
                metadata = {
                    "source_type": "csv",
                    "row_index": idx,
                    # Extract specific columns as metadata
                    # "column1": row.get("column1"),
                    # "column2": row.get("column2"),
                    # Add more metadata as needed...
                }
                metadata_list.append(metadata)
        
        # Example: Basic text metadata
        elif isinstance(content, str):
            # Simple metadata for text chunks
            chunk_indices = kwargs.get("chunk_indices", [0])
            
            for chunk_idx in chunk_indices:
                metadata = {
                    "source_type": "text",
                    "chunk_index": chunk_idx,
                    # Add more metadata as needed...
                }
                metadata_list.append(metadata)
        
        else:
            logger.warning(f"Unknown content type: {type(content)}")
            # Return empty metadata list or basic metadata
            metadata_list = [{"source_type": "unknown"}]
        
        logger.debug(f"Extracted metadata for {len(metadata_list)} chunks")
        return metadata_list


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     import pandas as pd
#     
#     # Test with DataFrame
#     df = pd.DataFrame({
#         "column1": ["value1", "value2"],
#         "column2": ["value3", "value4"]
#     })
#     
#     extractor = MyMetadataExtractor()
#     metadata = extractor.extract(df)
#     
#     print(f"Extracted metadata for {len(metadata)} rows")
#     for i, meta in enumerate(metadata):
#         print(f"Row {i}: {meta}")
