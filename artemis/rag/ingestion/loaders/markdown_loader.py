"""
Markdown loader for A.R.T.E.M.I.S.
"""

from pathlib import Path
from typing import Union

from artemis.utils import get_logger

logger = get_logger(__name__)


def load_md_text(path: Union[str, Path]) -> str:
    """
    Load Markdown file and return text content.
    
    Args:
        path: Path to Markdown file
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")
    
    logger.debug(f"Loading Markdown file: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"Loaded Markdown file: {len(text)} characters")
        return text
    except Exception as e:
        logger.exception(f"Failed to load Markdown file: {path}", exc_info=True)
        raise

