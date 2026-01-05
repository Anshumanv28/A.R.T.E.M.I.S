"""
Chunking registry and enums for A.R.T.E.M.I.S.

Provides file type enums, chunking strategy enums, and a registry pattern
for extensible chunking strategies.
"""

from enum import Enum
from typing import Dict, Callable, Tuple, List, Any

from artemis.utils import get_logger

logger = get_logger(__name__)


class FileType(str, Enum):
    """Supported file types for document ingestion."""
    CSV = "csv"
    PDF = "pdf"
    DOCX = "docx"
    MD = "md"
    TEXT = "text"


class ChunkStrategy(str, Enum):
    """Chunking strategies for document processing."""
    CSV_ROW = "csv_row"              # Row-based chunking for CSV files
    FIXED = "fixed"                  # Fixed size chunks, no overlap
    FIXED_OVERLAP = "fixed_overlap"  # Fixed size chunks with overlap
    SEMANTIC = "semantic"           # Embedding/sentence-aware chunking
    AGENTIC = "agentic"             # LLM/agent-driven chunking


# Registry for chunking strategies
CHUNKERS: Dict[ChunkStrategy, Callable[..., Tuple[List[str], List[Dict[str, Any]]]]] = {}


def register_chunker(strategy: ChunkStrategy):
    """
    Decorator to register a chunker function for a strategy.
    
    Use this decorator to register custom chunkers. The decorated function
    should take raw input (DataFrame, text, etc.) and return (documents, metadata).
    
    Args:
        strategy: ChunkStrategy enum value to register
        
    Example:
        >>> @register_chunker(ChunkStrategy.FIXED_OVERLAP)
        >>> def my_chunker(text: str, chunk_size: int = 800) -> Tuple[List[str], List[Dict]]:
        >>>     # chunking logic
        >>>     return docs, metadata
    """
    def wrapper(func: Callable[..., Tuple[List[str], List[Dict[str, Any]]]]):
        CHUNKERS[strategy] = func
        logger.debug(f"Registered chunker for strategy: {strategy.value}")
        return func
    return wrapper


# Default chunking strategy mapping by file type
DEFAULT_CHUNK_FOR_FILETYPE: Dict[FileType, ChunkStrategy] = {
    FileType.CSV: ChunkStrategy.CSV_ROW,
    FileType.PDF: ChunkStrategy.FIXED_OVERLAP,
    FileType.DOCX: ChunkStrategy.FIXED_OVERLAP,
    FileType.MD: ChunkStrategy.SEMANTIC,
    FileType.TEXT: ChunkStrategy.FIXED_OVERLAP,
}

