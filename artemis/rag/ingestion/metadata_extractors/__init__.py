"""
Metadata extractors for A.R.T.E.M.I.S.

Provides format-specific metadata extraction for different file types.
"""

from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.rag.ingestion.metadata_extractors.csv_extractor import CSVMetadataExtractor
from artemis.rag.ingestion.metadata_extractors.pdf_extractor import PDFMetadataExtractor
from artemis.rag.ingestion.metadata_extractors.docx_extractor import DOCXMetadataExtractor
from artemis.rag.ingestion.metadata_extractors.markdown_extractor import MarkdownMetadataExtractor
from artemis.rag.ingestion.metadata_extractors.text_extractor import TextMetadataExtractor

__all__ = [
    "MetadataExtractor",
    "CSVMetadataExtractor",
    "PDFMetadataExtractor",
    "DOCXMetadataExtractor",
    "MarkdownMetadataExtractor",
    "TextMetadataExtractor",
]

