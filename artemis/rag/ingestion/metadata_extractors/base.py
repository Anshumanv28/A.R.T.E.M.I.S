"""
Base metadata extractor interface for A.R.T.E.M.I.S.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class MetadataExtractor(ABC):
    """Abstract base class for metadata extractors."""
    
    @abstractmethod
    def extract(self, content: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract metadata for each chunk.
        
        Args:
            content: The raw content (DataFrame, text, etc.)
            **kwargs: Additional arguments specific to the extractor
            
        Returns:
            List of metadata dictionaries (one per chunk)
        """
        pass

