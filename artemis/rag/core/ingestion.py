"""
Generic file ingestion helper for A.R.T.E.M.I.S.

Provides a unified interface for ingesting various file types into the vector store.
Orchestrates the load → chunk → index pipeline.
"""

from pathlib import Path
from typing import Optional, Any, Union

from artemis.rag.core.chunker import (
    FileType,
    ChunkStrategy,
    CHUNKERS,
    DEFAULT_CHUNK_FOR_FILETYPE,
)
from artemis.rag.core.loaders import (
    load_csv,
    load_pdf_text,
    load_docx_text,
    load_md_text,
    load_text,
)
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.document_converter import DocumentSchema
from artemis.utils import get_logger

logger = get_logger(__name__)

# Auto-register chunkers when ingestion module is imported
try:
    from artemis.rag.core.chunkers import (  # noqa: F401
        csv_row_chunker,
        fixed_chunker,
        fixed_overlap_chunker,
        semantic_chunker,
        agentic_chunker,
    )
except ImportError:
    # Chunkers may not be available if dependencies are missing
    pass


def ingest_file(
    path: Union[str, Path],
    file_type: FileType,
    indexer: Indexer,
    chunk_strategy: Optional[ChunkStrategy] = None,
    schema: Optional[DocumentSchema] = None,
    **chunk_kwargs: Any,
) -> None:
    """
    Ingest a file into the vector store using the appropriate loader and chunker.
    
    This is the main entry point for file ingestion. It handles:
    1. Loading the file based on file type
    2. Chunking using the specified or default strategy
    3. Indexing the chunks into the vector store
    
    Args:
        path: Path to the file to ingest
        file_type: FileType enum indicating the file format
        indexer: Indexer instance to use for storing documents
        chunk_strategy: Optional ChunkStrategy. If None, uses default for file type.
        schema: Optional DocumentSchema for CSV files (only used with CSV_ROW strategy)
        **chunk_kwargs: Additional keyword arguments passed to the chunker
                       (e.g., chunk_size, overlap for fixed chunkers)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If chunk_strategy is not registered
        ImportError: If required dependencies for file type are missing
        
    Example:
        >>> from artemis.rag.core import Indexer, FileType, ChunkStrategy
        >>> indexer = Indexer(collection_name="docs")
        >>> # Simple usage with defaults
        >>> ingest_file("document.pdf", FileType.PDF, indexer)
        >>> # Override chunking strategy
        >>> ingest_file("document.pdf", FileType.PDF, indexer, 
        ...             chunk_strategy=ChunkStrategy.SEMANTIC)
        >>> # With chunker parameters
        >>> ingest_file("document.txt", FileType.TEXT, indexer,
        ...             chunk_size=1500, overlap=300)
        >>> # CSV with schema
        >>> ingest_file("restaurants.csv", FileType.CSV, indexer,
        ...             schema=DocumentSchema.RESTAURANT)
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    logger.info(f"Ingesting file: {path} (type: {file_type.value})")
    
    # Step 1: Load file based on type
    logger.debug(f"Loading {file_type.value} file: {path}")
    if file_type == FileType.CSV:
        raw = load_csv(path)
    elif file_type == FileType.PDF:
        raw = load_pdf_text(path)
    elif file_type == FileType.DOCX:
        raw = load_docx_text(path)
    elif file_type == FileType.MD:
        raw = load_md_text(path)
    elif file_type == FileType.TEXT:
        raw = load_text(path)
    else:
        raise ValueError(f"Unsupported file type: {file_type.value}")
    
    logger.debug(f"Loaded {file_type.value} file: {len(str(raw)) if isinstance(raw, str) else len(raw)} items")
    
    # Step 2: Choose chunking strategy
    strategy = chunk_strategy or DEFAULT_CHUNK_FOR_FILETYPE[file_type]
    logger.debug(f"Using chunking strategy: {strategy.value}")
    
    if strategy not in CHUNKERS:
        available_strategies = [s.value for s in CHUNKERS.keys()]
        raise ValueError(
            f"Chunking strategy '{strategy.value}' is not registered. "
            f"Available strategies: {available_strategies}. "
            "You can register a custom chunker:\n"
            "  from artemis.rag.core.chunker import register_chunker, ChunkStrategy\n"
            f"  @register_chunker(ChunkStrategy('{strategy.value}'))\n"
            "  def my_chunker(raw, **kwargs): ..."
        )
    
    chunker = CHUNKERS[strategy]
    
    # Step 3: Chunk the loaded content
    logger.debug(f"Chunking content using {strategy.value} strategy")
    try:
        # CSV chunker needs special handling (takes DataFrame + optional schema + csv_path)
        if file_type == FileType.CSV and strategy == ChunkStrategy.CSV_ROW:
            documents, metadata = chunker(raw, schema=schema, csv_path=path, **chunk_kwargs)
        else:
            # Other chunkers take text string
            documents, metadata = chunker(raw, **chunk_kwargs)
    except Exception as e:
        logger.exception(f"Error chunking file: {path}", exc_info=True)
        raise
    
    logger.info(f"Chunked into {len(documents)} documents")
    
    # Step 4: Index documents
    logger.debug(f"Indexing {len(documents)} documents")
    indexer.add_documents(documents, metadata)
    logger.info(f"Successfully ingested {len(documents)} documents from {path}")


# Convenience functions for each file type
def ingest_csv(
    path: Union[str, Path],
    indexer: Indexer,
    schema: Optional[DocumentSchema] = None,
    chunk_strategy: Optional[ChunkStrategy] = None,
    **chunk_kwargs: Any,
) -> None:
    """Convenience function to ingest a CSV file."""
    ingest_file(path, FileType.CSV, indexer, chunk_strategy=chunk_strategy, schema=schema, **chunk_kwargs)


def ingest_pdf(
    path: Union[str, Path],
    indexer: Indexer,
    chunk_strategy: Optional[ChunkStrategy] = None,
    **chunk_kwargs: Any,
) -> None:
    """Convenience function to ingest a PDF file."""
    ingest_file(path, FileType.PDF, indexer, chunk_strategy=chunk_strategy, **chunk_kwargs)


def ingest_docx(
    path: Union[str, Path],
    indexer: Indexer,
    chunk_strategy: Optional[ChunkStrategy] = None,
    **chunk_kwargs: Any,
) -> None:
    """Convenience function to ingest a DOCX file."""
    ingest_file(path, FileType.DOCX, indexer, chunk_strategy=chunk_strategy, **chunk_kwargs)


def ingest_md(
    path: Union[str, Path],
    indexer: Indexer,
    chunk_strategy: Optional[ChunkStrategy] = None,
    **chunk_kwargs: Any,
) -> None:
    """Convenience function to ingest a Markdown file."""
    ingest_file(path, FileType.MD, indexer, chunk_strategy=chunk_strategy, **chunk_kwargs)


def ingest_text(
    path: Union[str, Path],
    indexer: Indexer,
    chunk_strategy: Optional[ChunkStrategy] = None,
    **chunk_kwargs: Any,
) -> None:
    """Convenience function to ingest a text file."""
    ingest_file(path, FileType.TEXT, indexer, chunk_strategy=chunk_strategy, **chunk_kwargs)

