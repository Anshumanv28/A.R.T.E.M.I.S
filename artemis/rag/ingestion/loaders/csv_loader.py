"""
CSV loader for A.R.T.E.M.I.S.
"""

from pathlib import Path
from typing import Union

import pandas as pd

from artemis.utils import get_logger

logger = get_logger(__name__)


def load_csv(path: Union[str, Path]) -> pd.DataFrame:
    """
    Load CSV file as pandas DataFrame.
    
    Args:
        path: Path to CSV file
        
    Returns:
        pandas DataFrame
        
    Raises:
        FileNotFoundError: If file doesn't exist
        pd.errors.EmptyDataError: If CSV is empty
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    logger.debug(f"Loading CSV file: {path}")
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.exception(f"Failed to load CSV file: {path}", exc_info=True)
        raise

