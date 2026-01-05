"""
File loaders for A.R.T.E.M.I.S.

Provides file type-specific loaders that extract raw content from various
file formats. Handles missing dependencies gracefully.
"""

from artemis.rag.ingestion.loaders.csv_loader import load_csv
from artemis.rag.ingestion.loaders.pdf_loader import load_pdf_text
from artemis.rag.ingestion.loaders.docx_loader import load_docx_text
from artemis.rag.ingestion.loaders.markdown_loader import load_md_text
from artemis.rag.ingestion.loaders.text_loader import load_text

__all__ = [
    "load_csv",
    "load_pdf_text",
    "load_docx_text",
    "load_md_text",
    "load_text",
]

