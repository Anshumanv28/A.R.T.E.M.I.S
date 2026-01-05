"""
CSV metadata extractor for A.R.T.E.M.I.S.
"""

import pandas as pd
from typing import List, Dict, Any

from artemis.rag.ingestion.metadata_extractors.base import MetadataExtractor
from artemis.utils import get_logger

logger = get_logger(__name__)


class CSVMetadataExtractor(MetadataExtractor):
    """Extract metadata from CSV rows."""
    
    def extract(self, df: pd.DataFrame, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract row data as metadata.
        
        Args:
            df: pandas DataFrame containing CSV data
            **kwargs: Additional arguments (not used)
            
        Returns:
            List of dictionaries containing row data for filtering
        """
        metadata_list = []
        for idx, row in df.iterrows():
            metadata = {}
            for col_name in df.columns:
                value = row.get(col_name)
                metadata[col_name] = value if not pd.isna(value) else None
            metadata_list.append(metadata)
        
        logger.debug(f"Extracted metadata for {len(metadata_list)} CSV rows")
        return metadata_list

