"""
Text loader for A.R.T.E.M.I.S.
"""

from pathlib import Path
from typing import Union

from artemis.utils import get_logger

logger = get_logger(__name__)


def load_text(path: Union[str, Path]) -> str:
    """
    Load plain text file.
    
    Args:
        path: Path to text file
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")
    
    logger.debug(f"Loading text file: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"Loaded text file: {len(text)} characters")
        return text
    except Exception as e:
        logger.exception(f"Failed to load text file: {path}", exc_info=True)
        raise

