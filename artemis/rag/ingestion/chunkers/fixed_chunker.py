"""
Fixed-size chunking strategies for A.R.T.E.M.I.S.

Provides fixed-size chunking with and without overlap for text documents.
"""

from typing import List, Dict, Tuple, Any

from artemis.rag.ingestion.chunkers.registry import register_chunker, ChunkStrategy
from artemis.utils import get_logger

logger = get_logger(__name__)


@register_chunker(ChunkStrategy.FIXED)
def fixed_chunker(
    text: str,
    chunk_size: int = 1000,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Chunk text into fixed-size chunks without overlap.
    
    Splits text into chunks of approximately chunk_size characters,
    breaking at word boundaries when possible.
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk in characters (default: 1000)
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of text chunks
        - metadata: List of metadata dicts with chunk index and position info
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to fixed_chunker")
        return [], []
    
    logger.debug(f"Chunking text into fixed-size chunks (size={chunk_size})")
    
    documents = []
    metadata_list = []
    
    # Split text into words to break at word boundaries
    words = text.split()
    current_chunk = []
    current_size = 0
    chunk_idx = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        
        # If adding this word would exceed chunk size, finalize current chunk
        if current_size + word_size > chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            documents.append(chunk_text)
            metadata_list.append({
                "chunk_index": chunk_idx,
                "chunk_size": len(chunk_text),
                "strategy": ChunkStrategy.FIXED.value,
            })
            chunk_idx += 1
            current_chunk = []
            current_size = 0
        
        current_chunk.append(word)
        current_size += word_size
    
    # Add remaining chunk if any
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        documents.append(chunk_text)
        metadata_list.append({
            "chunk_index": chunk_idx,
            "chunk_size": len(chunk_text),
            "strategy": ChunkStrategy.FIXED.value,
        })
    
    logger.info(f"Created {len(documents)} fixed-size chunks")
    return documents, metadata_list


@register_chunker(ChunkStrategy.FIXED_OVERLAP)
def fixed_overlap_chunker(
    text: str,
    chunk_size: int = 800,
    overlap: int = 200,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Chunk text into fixed-size chunks with overlap.
    
    Splits text into chunks of approximately chunk_size characters with
    overlap characters between chunks. This helps maintain context across
    chunk boundaries.
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk in characters (default: 800)
        overlap: Number of characters to overlap between chunks (default: 200)
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of text chunks
        - metadata: List of metadata dicts with chunk index and position info
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to fixed_overlap_chunker")
        return [], []
    
    if overlap >= chunk_size:
        logger.warning(f"Overlap ({overlap}) >= chunk_size ({chunk_size}), reducing overlap")
        overlap = chunk_size // 4
    
    logger.debug(f"Chunking text with overlap (size={chunk_size}, overlap={overlap})")
    
    documents = []
    metadata_list = []
    
    # Split text into words to break at word boundaries
    words = text.split()
    chunk_idx = 0
    start_idx = 0
    
    while start_idx < len(words):
        # Collect words for this chunk
        current_chunk = []
        current_size = 0
        end_idx = start_idx
        
        # Build chunk up to chunk_size
        while end_idx < len(words):
            word = words[end_idx]
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > chunk_size and current_chunk:
                break
            
            current_chunk.append(word)
            current_size += word_size
            end_idx += 1
        
        # Create chunk text
        chunk_text = " ".join(current_chunk)
        documents.append(chunk_text)
        metadata_list.append({
            "chunk_index": chunk_idx,
            "chunk_size": len(chunk_text),
            "strategy": ChunkStrategy.FIXED_OVERLAP.value,
            "overlap": overlap,
        })
        
        # Move start position forward, accounting for overlap
        # Calculate how many words to skip to achieve overlap
        if end_idx >= len(words):
            break
        
        # Find overlap point: go back by overlap characters
        overlap_chars = 0
        overlap_words = []
        for i in range(end_idx - 1, start_idx - 1, -1):
            if i < 0:
                break
            word = words[i]
            word_size = len(word) + 1
            if overlap_chars + word_size > overlap:
                break
            overlap_words.insert(0, word)
            overlap_chars += word_size
        
        # Start next chunk from the overlap point
        start_idx = end_idx - len(overlap_words)
        chunk_idx += 1
    
    logger.info(f"Created {len(documents)} fixed-size chunks with overlap")
    return documents, metadata_list

