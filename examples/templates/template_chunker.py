"""
Template: Custom Chunking Strategy for A.R.T.E.M.I.S.

This template shows how to create a custom chunking strategy.
Copy this file and customize it for your specific chunking needs.

Usage:
1. Copy this file to your project (e.g., my_project/my_chunker.py)
2. Customize the chunking logic
3. Import it in your code before using
4. Use it with ingest_file()

Example:
    from my_project.my_chunker import STRATEGY
    from artemis.rag import ingest_file, FileType, Indexer
    
    indexer = Indexer()
    ingest_file("file.pdf", FileType.PDF, indexer, chunk_strategy=STRATEGY)
"""

from typing import List, Dict, Tuple, Any
from artemis.rag.ingestion.chunkers.registry import (
    register_chunker,
    ChunkStrategy
)
from artemis.utils import get_logger

logger = get_logger(__name__)

# TODO: Choose or create your chunking strategy
# Option 1: Use existing strategy
# STRATEGY = ChunkStrategy.SEMANTIC  # or FIXED, FIXED_OVERLAP, etc.

# Option 2: Create custom strategy
STRATEGY = ChunkStrategy("my_custom_chunker")


@register_chunker(STRATEGY)
def my_custom_chunker(
    content: Any,  # DataFrame for CSV, str for text files
    **kwargs
) -> Tuple[List[str], List[Dict]]:
    """
    Custom chunking logic.
    
    TODO: Update this docstring with your chunker's description.
    
    Args:
        content: 
            - pandas.DataFrame for CSV files
            - str for text files (PDF, DOCX, MD, TEXT)
        **kwargs: Additional parameters
            - chunk_size: int (default: 800) - Size of chunks in characters
            - overlap: int (default: 200) - Overlap between chunks
            - schema: DocumentSchema (for CSV files) - Optional schema
            - Other custom parameters
    
    Returns:
        Tuple of (documents, metadata_list) where:
        - documents: List of chunked text strings
        - metadata_list: List of metadata dictionaries (one per chunk)
    """
    documents = []
    metadata_list = []
    
    # TODO: Get parameters from kwargs
    chunk_size = kwargs.get("chunk_size", 800)
    overlap = kwargs.get("overlap", 200)
    
    # Handle text files (PDF, DOCX, MD, TEXT)
    if isinstance(content, str):
        logger.debug(f"Chunking text content (length: {len(content)})")
        
        # TODO: Implement your text chunking logic
        # Example: Fixed-size chunking with overlap
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(content):
                break
        
        # Create documents and metadata
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadata_list.append({
                "chunk_index": i,
                "source_type": "text",
                "chunk_size": len(chunk),
                "start_position": i * (chunk_size - overlap),
                # Add more metadata as needed...
            })
        
        logger.info(f"Created {len(documents)} text chunks")
    
    # Handle CSV files (DataFrame)
    elif hasattr(content, 'iterrows'):  # pandas.DataFrame
        logger.debug(f"Chunking CSV content ({len(content)} rows)")
        
        # TODO: Implement your CSV chunking logic
        # Example: Row-based chunking
        for idx, row in content.iterrows():
            # TODO: Format row as document
            # You might want to use a CSV schema converter here
            # or format rows directly
            
            # Simple example: convert row to text
            doc_parts = {}
            for col in content.columns:
                value = row.get(col, "")
                if pd.notna(value):
                    doc_parts[col] = str(value)
            
            # Format as document (you might want to use format_doc from converters)
            doc_text = ". ".join([f"{k}: {v}" for k, v in doc_parts.items()])
            if doc_text:
                doc_text += "."
            
            documents.append(doc_text)
            metadata_list.append({
                "row_index": idx,
                "source_type": "csv",
                # Add row-specific metadata...
            })
        
        logger.info(f"Created {len(documents)} CSV row chunks")
    
    else:
        raise ValueError(f"Unsupported content type: {type(content)}")
    
    logger.info(f"Chunking complete: {len(documents)} chunks created")
    return documents, metadata_list


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     from artemis.rag import ingest_file, FileType, Indexer
#     
#     # Test with text file
#     indexer = Indexer()
#     ingest_file(
#         "path/to/your/file.pdf",
#         FileType.PDF,
#         indexer,
#         chunk_strategy=STRATEGY,
#         chunk_size=1000,
#         overlap=200
#     )
