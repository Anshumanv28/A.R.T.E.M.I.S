"""
PDF loader for A.R.T.E.M.I.S.
"""

from pathlib import Path
from typing import Union

from artemis.utils import get_logger

logger = get_logger(__name__)


def load_pdf_text(path: Union[str, Path]) -> str:
    """
    Load PDF file and extract text content.
    
    Args:
        path: Path to PDF file
        
    Returns:
        Extracted text content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ImportError: If required PDF library is not installed
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    logger.debug(f"Loading PDF file: {path}")
    
    # Try pdfplumber first (better text extraction)
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = "\n\n".join(text_parts)
        logger.info(f"Loaded PDF with {len(pdf.pages)} pages using pdfplumber")
        return text
    except ImportError:
        logger.debug("pdfplumber not available, trying PyPDF2")
    
    # Fallback to PyPDF2
    try:
        import PyPDF2
        text_parts = []
        with open(path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = "\n\n".join(text_parts)
        logger.info(f"Loaded PDF with {len(pdf_reader.pages)} pages using PyPDF2")
        return text
    except ImportError:
        raise ImportError(
            "PDF loading requires either 'pdfplumber' or 'PyPDF2'. "
            "Install with: pip install pdfplumber or pip install PyPDF2"
        )
    except Exception as e:
        logger.exception(f"Failed to load PDF file: {path}", exc_info=True)
        raise

