"""
Ingestion pipeline for A.R.T.E.M.I.S.

Provides file ingestion, chunking, and document processing capabilities.
"""

from artemis.rag.ingestion.ingestion import (
    ingest_file,
    ingest_csv,
    ingest_pdf,
    ingest_docx,
    ingest_md,
    ingest_text,
)
from artemis.rag.ingestion.chunkers.registry import (
    FileType,
    ChunkStrategy,
    CHUNKERS,
    DEFAULT_CHUNK_FOR_FILETYPE,
    register_chunker,
)
from artemis.rag.ingestion.converters.csv_converter import (
    DocumentSchema,
    CSV_CONVERTERS,
    register_csv_schema,
    format_doc,
    csv_to_documents,
)

__all__ = [
    "ingest_file",
    "ingest_csv",
    "ingest_pdf",
    "ingest_docx",
    "ingest_md",
    "ingest_text",
    "FileType",
    "ChunkStrategy",
    "CHUNKERS",
    "DEFAULT_CHUNK_FOR_FILETYPE",
    "register_chunker",
    "DocumentSchema",
    "CSV_CONVERTERS",
    "register_csv_schema",
    "format_doc",
    "csv_to_documents",
]

